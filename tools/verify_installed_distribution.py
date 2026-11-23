"""Check that an installed distribution is byte-identical to a git commit.

Every file the distribution's RECORD lists under its packages (dist-info and
bytecode excepted) is compared with the git blob at the same path in COMMIT.
Exit 0 only if all compared files are identical, none is missing from the
commit, and nothing under the packages is on disk without being in RECORD.

Usage: python -I tools/verify_installed_distribution.py DIST REPO COMMIT [--out FILE]
Run it with the interpreter of the environment the distribution is installed in.
"""
import argparse
import hashlib
import importlib.metadata as md
import json
import pathlib
import subprocess
import sys


def git_tree(repo, commit):
    out = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", commit],
                         check=True, capture_output=True).stdout
    tree = {}
    for line in out.split(b"\0"):
        if line:
            meta, path = line.split(b"\t", 1)
            _mode, typ, sha = meta.split()
            if typ == b"blob":
                tree[path.decode()] = sha.decode()
    return tree


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("dist")
    p.add_argument("repo")
    p.add_argument("commit")
    p.add_argument("--out", default="")
    a = p.parse_args(argv)
    d = md.distribution(a.dist)
    tree = git_tree(a.repo, a.commit)
    same, differ, absent, skipped = [], [], [], 0
    packages = set()
    for f in d.files or ():
        path = str(f)
        if ".dist-info/" in path or "__pycache__" in path or path.endswith(".pyc") or path.startswith(".."):
            skipped += 1
            continue
        packages.add(path.split("/", 1)[0])
        data = pathlib.Path(f.locate()).read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        (same if tree.get(path) == blob else differ if path in tree else absent).append(path)
    site = pathlib.Path(d.locate_file(""))
    listed = {str(f) for f in d.files or ()}
    unlisted = sorted(str(x.relative_to(site)) for pkg in sorted(packages)
                      for x in (site / pkg).rglob("*")
                      if x.is_file() and "__pycache__" not in x.parts and str(x.relative_to(site)) not in listed)
    report = {"distribution": a.dist, "version": d.version, "commit": a.commit,
              "files_compared": len(same) + len(differ) + len(absent),
              "identical_to_git_blob": len(same), "different": differ, "not_in_git": absent,
              "skipped": skipped, "on_disk_not_in_RECORD": unlisted}
    ok = report["files_compared"] > 0 and not differ and not absent and not unlisted
    report["identical"] = ok
    text = json.dumps(report, indent=1)
    if a.out:
        pathlib.Path(a.out).write_text(text + "\n")
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
