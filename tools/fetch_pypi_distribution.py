"""Download the archives of a pinned PyPI release and their PEP 740 provenance.

Reads the `--hash=sha256:...` values of a pins file (pip requirements format,
one project at one exact version), fetches the release's files from the PyPI
JSON API, refuses any file whose sha256 is not pinned or any pinned hash with no
file, and saves each archive with its provenance object from the PyPI
integrity API. It verifies nothing cryptographically: run
`python -m pypi_attestations verify pypi --repository <repo> --provenance-file
<file>.provenance.json <file>` on each archive afterwards.

Usage: python -I tools/fetch_pypi_distribution.py PINS OUTDIR
"""
import hashlib
import json
import pathlib
import re
import sys
import urllib.request

PYPI = "https://pypi.org"


def get(url, accept=None):
    req = urllib.request.Request(url, headers={"Accept": accept} if accept else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main(argv=None):
    pins_path, out = (argv or sys.argv[1:])[:2]
    text = pathlib.Path(pins_path).read_text()
    spec = re.search(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", text, re.M)
    if not spec:
        raise SystemExit(f"no 'project==version' line in {pins_path}")
    project, version = spec.groups()
    pinned = set(re.findall(r"--hash=sha256:([0-9a-f]{64})", text))
    if not pinned:
        raise SystemExit(f"no sha256 pin in {pins_path}")
    meta = json.loads(get(f"{PYPI}/pypi/{project}/{version}/json"))
    files = {u["digests"]["sha256"]: u for u in meta["urls"]}
    if set(files) != pinned:
        raise SystemExit(f"PyPI files and pins differ: published {sorted(files)}, pinned {sorted(pinned)}")
    outdir = pathlib.Path(out)
    outdir.mkdir(parents=True, exist_ok=True)
    record = {"project": project, "version": version, "files": []}
    for digest, u in sorted(files.items(), key=lambda kv: kv[1]["filename"]):
        data = get(u["url"])
        got = hashlib.sha256(data).hexdigest()
        if got != digest:
            raise SystemExit(f"{u['filename']}: downloaded sha256 {got} != pinned {digest}")
        (outdir / u["filename"]).write_bytes(data)
        prov = get(f"{PYPI}/integrity/{project}/{version}/{u['filename']}/provenance",
                   accept="application/vnd.pypi.integrity.v1+json")
        (outdir / f"{u['filename']}.provenance.json").write_bytes(prov)
        record["files"].append({"filename": u["filename"], "sha256": got,
                                "upload_time": u.get("upload_time_iso_8601"), "url": u["url"]})
    (outdir / "pypi-files.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
