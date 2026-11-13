"""Compare the comments (subject and text) of two submission pages, byte for byte.

Usage:
    python3 diff_submit_pages.py posted_or_old.html fresh.html

Use before posting: dump the finals fresh from the database, build fresh.html from them, and compare it
with the page the author copies from. Exit 0 only when every comment is identical.
"""
import difflib
import json
import re
import sys
from pathlib import Path

DATA_RE = re.compile(r"const DATA = (.*?);\n", re.S)


def comments(path: Path):
    m = DATA_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"{path}: no 'const DATA = ...;' line; not a submission page")
    data = json.loads(m.group(1))
    if not isinstance(data, list) or not all(isinstance(c, dict) and {"subject", "text"} <= set(c) for c in data):
        raise SystemExit(f"{path}: DATA is not a list of comments with subject and text")
    return [(c["subject"], c["text"]) for c in data]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    a_path, b_path = map(Path, sys.argv[1:])
    a, b = comments(a_path), comments(b_path)
    same = True
    if len(a) != len(b):
        print(f"comment count differs: {len(a)} in {a_path.name}, {len(b)} in {b_path.name}")
        same = False
    for k, (x, y) in enumerate(zip(a, b), 1):
        if x == y:
            print(f"{k}. identical  {x[0]} ({len(x[1].encode())} bytes)")
            continue
        same = False
        print(f"{k}. DIFFERENT  {x[0]!r} vs {y[0]!r}")
        sys.stdout.writelines(difflib.unified_diff(x[1].splitlines(True), y[1].splitlines(True), a_path.name, b_path.name, n=1))
        print()
    print("all comments identical" if same else "comments differ")
    raise SystemExit(0 if same else 1)


if __name__ == "__main__":
    main()
