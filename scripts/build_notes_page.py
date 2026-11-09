"""Build the rebuttal notes page from points.json.

Usage:
    python3 build_notes_page.py points.json reviews.txt templates/notes_page.html out.html

points.json holds the reviewers and the points to answer (schema in SKILL.md). Every quoted
excerpt must appear verbatim (whitespace-insensitive) in reviews.txt, the plain-text dump of
the review page; the build stops on the first excerpt that does not.
"""
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return " ".join(s.split())


def sentences(text: str) -> int:
    return max(1, len(re.findall(r"[.?!](?:\s|$)", text)))


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    points_path, reviews_path, template_path, out_path = map(Path, sys.argv[1:])
    spec = json.loads(points_path.read_text(encoding="utf-8"))
    reviews = norm(reviews_path.read_text(encoding="utf-8"))

    def check(where: str, q: dict) -> dict:
        if not isinstance(q, dict) or not q.get("label") or not q.get("text"):
            raise SystemExit(f"{where}: each excerpt needs non-empty 'label' and 'text', got {q!r:.120}")
        text = norm(q["text"])
        if text not in reviews:
            raise SystemExit(f"{where}: excerpt is not verbatim in {reviews_path.name}: {text[:90]!r}")
        return {"label": q["label"], "text": text}

    if not spec.get("reviewers"):
        raise SystemExit("points.json: 'reviewers' is missing or empty")
    data = {"title": spec.get("title") or "Rebuttal Notes", "pageId": spec.get("pageId") or points_path.stem,
            "reviewers": []}
    seen = set()
    for r in spec["reviewers"]:
        name = r.get("name")
        if not name or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise SystemExit(f"reviewer name must be letters/digits/_/-, got {name!r}")
        if name.lower() in seen:
            raise SystemExit(f"duplicate reviewer name {name!r}")
        seen.add(name.lower())
        strengths = [check(f"{name} strengths[{i}]", q) for i, q in enumerate(r.get("strengths", []))]
        points = []
        for i, p in enumerate(r.get("points", []), 1):
            if not p.get("title") or not p.get("quotes"):
                raise SystemExit(f"{name} point {i}: needs 'title' and at least one quote")
            quotes = [check(f"{name} point {i} quotes[{k}]", q) for k, q in enumerate(p["quotes"])]
            points.append({"id": f"{name.lower()}-{i}", "title": p["title"],
                           "sentences": sum(sentences(q["text"]) for q in quotes), "quotes": quotes})
        if not points:
            raise SystemExit(f"{name}: no points")
        data["reviewers"].append({"name": name, "score": r.get("score", ""), "openId": f"{name.lower()}-open",
                                  "strengths": strengths, "points": points})

    page = template_path.read_text(encoding="utf-8")
    if "/*__DATA__*/null" not in page:
        raise SystemExit(f"{template_path}: data placeholder not found")
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out_path.write_text(page, encoding="utf-8")
    print(f"wrote {out_path}: " + ", ".join(f"{r['name']} {len(r['points'])} points" for r in data["reviewers"]))


if __name__ == "__main__":
    main()
