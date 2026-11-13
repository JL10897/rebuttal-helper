"""Check the Appendix / Table / Figure / Section numbers the replies cite against the submitted paper.

Usage:
    python3 check_labels.py --repo PAPER_REPO --commit SHA --main main.tex --page submit.html [--tectonic PATH]

Compiles the paper's LaTeX source at the given commit (the version the reviewers read) in a temporary
directory, reads the labels from its .aux files, and prints every cited number next to what the reply
says and what that number is in the paper (label, title or caption, page). The local build and its
old .aux files are never used. Exit 1 if a cited number does not exist in the paper.

Tectonic is found via --tectonic, else the TECTONIC environment variable, else PATH. The paper needs
hyperref, whose label anchors tell tables, figures and sections apart.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ITEM = r"[A-Z]?\d+(?:\.\d+)*|[A-Z](?:\.\d+)*"
SEP = r"\s*(?:,|and|&|–|-|to)\s*"
CITE = re.compile(rf"\b(Appendix|Appendices|App\.|Tables?|Tab\.|Figures?|Fig\.|Sections?|Sec\.)\s*((?:{ITEM})(?:{SEP}(?:{ITEM}))*)")
KIND = {"appendix": "Appendix", "appendices": "Appendix", "app.": "Appendix", "table": "Table", "tables": "Table",
        "tab.": "Table", "figure": "Figure", "figures": "Figure", "fig.": "Figure", "section": "Section",
        "sections": "Section", "sec.": "Section"}
SECTIONAL = ("part", "chapter", "section", "subsection", "subsubsection", "paragraph", "appendix")


def braced(s, i):
    """Return (content, index after) of the balanced {...} group starting at s[i]."""
    if s[i] != "{":
        raise ValueError(f"expected '{{' at {i}: {s[i:i + 30]!r}")
    depth, j = 0, i
    while True:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        depth += c == "{"
        depth -= c == "}"
        j += 1
        if depth == 0:
            return s[i + 1:j - 1], j


def read_labels(build: Path):
    labels = []
    for aux in sorted(build.rglob("*.aux")):
        s = aux.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\\newlabel\{", s, re.M):
            key, j = braced(s, m.end() - 1)
            body, _ = braced(s, j)
            fields, k = [], 0
            while k < len(body):
                if body[k] == "{":
                    f, k = braced(body, k)
                    fields.append(f)
                else:
                    k += 1
            if len(fields) < 4:
                raise SystemExit(f"{aux.name}: label {key!r} has no hyperref anchor; this check needs hyperref")
            number, page, title, anchor = fields[:4]
            kind = anchor.split(".")[0]
            labels.append({"key": key, "number": number, "page": page, "kind": kind,
                           "title": re.sub(r"\\relax\s*$", "", " ".join(title.split())).strip()})
    return labels


def expand(items_text):
    out = []
    for part in re.split(r"\s*(?:,|and|&)\s*", items_text):
        r = re.fullmatch(r"(\d+)\s*(?:–|-|to)\s*(\d+)", part)
        if r and int(r[1]) < int(r[2]):
            out += [str(n) for n in range(int(r[1]), int(r[2]) + 1)]
        elif part:
            out += [p for p in re.split(r"\s*(?:–|-|to)\s*", part) if p]
    return out


def matches(kind, number, lab):
    if lab["number"] != number:
        return False
    if kind == "Table":
        return lab["kind"] == "table"
    if kind == "Figure":
        return lab["kind"] == "figure"
    if kind == "Appendix":
        return lab["kind"].rstrip("*") in SECTIONAL and number[0].isalpha()
    return lab["kind"].rstrip("*") in SECTIONAL


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--main", required=True, help="main .tex file, relative to the repo root")
    ap.add_argument("--page", required=True, type=Path, help="submission page built by build_submit_page.py")
    ap.add_argument("--tectonic", default=os.environ.get("TECTONIC") or shutil.which("tectonic"))
    a = ap.parse_args()
    if not a.tectonic or not Path(a.tectonic).is_file():
        raise SystemExit(f"Tectonic not found ({a.tectonic!r}); pass --tectonic PATH or set TECTONIC")
    m = re.search(r"const DATA = (.*?);\n", a.page.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SystemExit(f"{a.page}: no 'const DATA = ...;' line; not a submission page")
    comments = json.loads(m.group(1))

    with tempfile.TemporaryDirectory(prefix="rebuttal-labels-") as tmp:
        build = Path(tmp)
        archive = subprocess.run(["git", "-C", str(a.repo), "archive", a.commit], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(build)], input=archive, check=True)
        main_tex = build / a.main
        if not main_tex.is_file():
            raise SystemExit(f"{a.main} not found in {a.repo} at {a.commit}")
        print(f"compiling {a.main} at {a.commit} with {a.tectonic} ...", flush=True)
        r = subprocess.run([a.tectonic, "--keep-intermediates", "--keep-logs", main_tex.name],
                           cwd=main_tex.parent, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"Tectonic failed (exit {r.returncode}):\n{r.stderr[-3000:]}")
        labels = read_labels(build)
    print(f"{len(labels)} labels in the paper at {a.commit}\n")

    bad, seen = 0, set()
    for c in comments:
        for cm in CITE.finditer(c["text"]):
            kind = KIND[cm[1].lower()]
            context = " ".join(c["text"][cm.start():cm.end() + 60].split())
            for number in expand(cm[2]):
                if (kind, number, c["subject"]) in seen:
                    continue
                seen.add((kind, number, c["subject"]))
                hits = [lab for lab in labels if matches(kind, number, lab)]
                print(f"{kind} {number}  [{c['subject']}]  reply: \"{context}...\"")
                if not hits:
                    bad += 1
                    print(f"    NOT FOUND in the paper\n")
                    continue
                for lab in hits:
                    print(f"    paper: \\label{{{lab['key']}}} ({lab['kind']}, p. {lab['page']}): {lab['title'][:110]}")
                print()
    print(f"{bad} cited number(s) not found" if bad else "every cited number exists in the paper; check that each title matches what the reply says")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
