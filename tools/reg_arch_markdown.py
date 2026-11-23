#!/usr/bin/env python3
"""Markdown transcription of the REG-ARCH candidate, generated from its DOCX and checked against it.

    python tools/reg_arch_markdown.py            # rewrite the Markdown from the DOCX
    python tools/reg_arch_markdown.py --check    # fail if the committed Markdown is stale or its text drifted

The DOCX in audits/reg-arch-v0.4.1/ is the frozen origin of the v0.4.1 candidate. The Markdown is a
transcription of it, kept so the text can be read, diffed and cited on GitHub. ``--check`` enforces two
things: regenerating gives the committed file byte for byte, and the words of the Markdown are the words
of the DOCX, in order. It says nothing about whether the specification is right, ratified or implemented.

Standard library only.
"""
from __future__ import annotations

import hashlib
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "audits" / "reg-arch-v0.4.1" / "REG-ARCH_v0.4.1-candidate.docx"
TARGET = ROOT / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HEADING = re.compile(r"(?i)^(?:heading|titre)\s*(\d)$")
# The lane diagram of section 2.3 is laid out with line breaks and box-drawing characters: keep it verbatim.
VERBATIM_AFTER_HEADING = "2.3. Articulation générale"
VERBATIM_UNTIL_PREFIX = "Les flèches représentent"


def _segments(paragraph):
    """(text, bold) pieces of a paragraph, in order."""
    out = []
    for run in paragraph.iter(W + "r"):
        props = run.find(W + "rPr")
        bold = False
        if props is not None:
            b = props.find(W + "b")
            bold = b is not None and b.get(W + "val", "true") not in ("0", "false")
        text = []
        for node in run:
            if node.tag == W + "t":
                text.append(node.text or "")
            elif node.tag == W + "tab":
                text.append("\t")
            elif node.tag in (W + "br", W + "cr"):
                text.append("\n")
        if text:
            out.append(("".join(text), bold))
    return out


def _plain(paragraph):
    return "".join(text for text, _ in _segments(paragraph))


def _inline(paragraph):
    """Paragraph text with bold runs marked; whitespace stays outside the markers."""
    merged = []
    for text, bold in _segments(paragraph):
        if merged and merged[-1][1] == bold:
            merged[-1][0] += text
        else:
            merged.append([text, bold])
    out = []
    for text, bold in merged:
        core = text.strip()
        if bold and core:
            lead = text[: len(text) - len(text.lstrip())]
            tail = text[len(text.rstrip()):]
            out.append(f"{lead}**{core}**{tail}")
        else:
            out.append(text)
    return " ".join("".join(out).split())


def _style(paragraph):
    props = paragraph.find(W + "pPr")
    if props is None:
        return "", None
    style = props.find(W + "pStyle")
    num = props.find(W + "numPr")
    num_id = None
    if num is not None and num.find(W + "numId") is not None:
        num_id = num.find(W + "numId").get(W + "val")
    return (style.get(W + "val", "") if style is not None else ""), num_id


def _ordered_lists(archive):
    """numId values whose first level is a numbered format rather than a bullet."""
    try:
        root = ET.fromstring(archive.read("word/numbering.xml"))
    except KeyError:
        return set()
    formats = {}
    for abstract in root.iter(W + "abstractNum"):
        level = abstract.find(W + "lvl")
        fmt = level.find(W + "numFmt") if level is not None else None
        formats[abstract.get(W + "abstractNumId")] = fmt.get(W + "val") if fmt is not None else "bullet"
    ordered = set()
    for num in root.iter(W + "num"):
        ref = num.find(W + "abstractNumId")
        if ref is not None and formats.get(ref.get(W + "val"), "bullet") != "bullet":
            ordered.add(num.get(W + "numId"))
    return ordered


def _cell(cell):
    text = " ".join(" ".join(_plain(p).split()) for p in cell.iter(W + "p"))
    return " ".join(text.split()).replace("|", "\\|")


def render(source: Path = SOURCE) -> str:
    data = source.read_bytes()
    archive = zipfile.ZipFile(source)
    body = ET.fromstring(archive.read("word/document.xml")).find(W + "body")
    ordered = _ordered_lists(archive)
    blocks, verbatim, in_verbatim, titled = [], [], False, False

    def flush_verbatim():
        nonlocal verbatim
        if verbatim:
            blocks.append(("verbatim", "\n".join(verbatim)))
        verbatim = []

    for node in body:
        if node.tag == W + "tbl":
            rows = [[_cell(c) for c in row.findall(W + "tc")] for row in node.iter(W + "tr")]
            rows = [r for r in rows if r]
            if rows:
                lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in rows[0]) + " |"]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                blocks.append(("table", "\n".join(lines)))
            continue
        if node.tag != W + "p":
            continue
        raw = _plain(node)
        if not raw.strip():
            continue
        style, num_id = _style(node)
        heading = HEADING.match(style)
        if in_verbatim:
            if heading or raw.strip().startswith(VERBATIM_UNTIL_PREFIX):
                in_verbatim = False
                flush_verbatim()
            else:
                verbatim.extend(line.rstrip() for line in raw.split("\n"))
                continue
        if heading:
            text = " ".join(raw.split())
            blocks.append(("heading", "#" * (int(heading.group(1)) + 1) + " " + text))
            in_verbatim = text == VERBATIM_AFTER_HEADING
        elif not titled:
            blocks.append(("heading", "# " + " ".join(raw.split())))
        elif num_id is not None or style.lower().startswith(("paragraphedeliste", "listparagraph")):
            blocks.append(("item", ("1. " if num_id in ordered else "- ") + _inline(node)))
        else:
            blocks.append(("para", _inline(node)))
        titled = True
    flush_verbatim()

    digest = hashlib.sha256(data).hexdigest()
    out = [
        "<!-- Generated by tools/reg_arch_markdown.py — do not edit by hand.",
        f"     Source: {source.relative_to(ROOT).as_posix()}",
        f"     sha256: {digest}",
        "     Status: v0.4.1 candidate, not ratified. See specs/reg-arch/README.md. -->",
        "",
    ]
    previous = None
    for kind, text in blocks:
        if previous is not None and not (kind == "item" and previous == "item"):
            out.append("")
        out.append("```text\n" + text + "\n```" if kind == "verbatim" else text)
        previous = kind
    return "\n".join(out) + "\n"


def _docx_words(source: Path) -> list[str]:
    body = ET.fromstring(zipfile.ZipFile(source).read("word/document.xml")).find(W + "body")
    return " ".join(_plain(p) for p in body.iter(W + "p")).split()


def _markdown_words(markdown: str) -> list[str]:
    words, in_comment = [], False
    for line in markdown.splitlines():
        if line.startswith("<!--"):
            in_comment = True
        if in_comment:
            in_comment = "-->" not in line
            continue
        if line.startswith("```") or re.fullmatch(r"\|(?: --- \|)+", line):
            continue
        if line.startswith("|"):
            line = " ".join(re.split(r"(?<!\\)\|", line)).replace("\\|", "|")
        else:
            line = re.sub(r"^(?:#{1,6} |- |1\. )", "", line)
        words.extend(line.replace("**", "").split())
    return words


def main(argv: list[str]) -> int:
    if not SOURCE.exists():
        print(f"FAIL {SOURCE.relative_to(ROOT).as_posix()} is missing: the transcription has no source to check against")
        return 1
    rendered = render()
    if "--check" not in argv:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(rendered, encoding="utf-8")
        print(f"wrote {TARGET.relative_to(ROOT).as_posix()} ({len(rendered.splitlines())} lines)")
        return 0
    problems = []
    if not TARGET.exists():
        problems.append(f"{TARGET.relative_to(ROOT).as_posix()} is missing: run tools/reg_arch_markdown.py")
    else:
        committed = TARGET.read_text(encoding="utf-8")
        if committed != rendered:
            problems.append("the committed Markdown differs from what the DOCX generates: it is stale or was edited by hand")
        source_words, markdown_words = _docx_words(SOURCE), _markdown_words(committed)
        if source_words != markdown_words:
            at = next((i for i, (a, b) in enumerate(zip(source_words, markdown_words)) if a != b),
                      min(len(source_words), len(markdown_words)))
            problems.append(
                f"text drift at word {at}: DOCX has {' '.join(source_words[at:at + 6])!r}, "
                f"Markdown has {' '.join(markdown_words[at:at + 6])!r}")
    for problem in problems:
        print("FAIL " + problem)
    if not problems:
        print(f"REG-ARCH Markdown matches its DOCX: {len(_docx_words(SOURCE))} words, byte-identical regeneration")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
