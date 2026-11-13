"""Build the compare page: the one workbench from notes to drafts to finals.

Usage:
    python3 build_compare_page.py points.json reviews.txt author_style.md out.html [--drafts DIR]

- points.json: the confirmed points (schema in SKILL.md). Every excerpt must be verbatim in reviews.txt.
- author_style.md: fills the style box when the page's database has no saved style yet.
- --drafts DIR: model drafts, one file per item, model and round: <item id>_v<N>_<model>.json holding
  {"model", "reply", "logic", "flags"}. Only the latest round of each item is shown; its columns are
  named by each file's "model". Without --drafts every card is in the notes state.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from points import PointsError, load_points  # noqa: E402

TEMPLATE = Path(__file__).parent.parent / "templates" / "compare_page.html"
DRAFT_RE = re.compile(r"(?P<item>[a-z0-9-]+)_v(?P<round>[1-9][0-9]*)_(?P<slug>[A-Za-z0-9.-]+)\.json")
DRAFT_KEYS = {"model", "reply", "logic", "flags"}


def load_drafts(drafts_dir: Path, item_ids):
    """Return {item id: {"round": N, "drafts": [...]}} for the latest round of each item.
    The round number stays in file names only; the page shows the latest round without it."""
    found = {}
    for f in sorted(drafts_dir.iterdir()):
        if f.name.startswith("."):
            continue
        m = DRAFT_RE.fullmatch(f.name)
        if not m:
            raise SystemExit(f"{f}: not a draft file name (<item id>_v<N>_<model>.json)")
        if m["item"] not in item_ids:
            raise SystemExit(f"{f}: unknown item id {m['item']!r}")
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{f}: not valid JSON: {e}") from e
        if not isinstance(d, dict) or set(d) != DRAFT_KEYS:
            raise SystemExit(f"{f}: expected exactly the keys {sorted(DRAFT_KEYS)}, got {sorted(d) if isinstance(d, dict) else d!r}")
        if not isinstance(d["model"], str) or not d["model"].strip():
            raise SystemExit(f"{f}: 'model' must be a non-empty string")
        if not isinstance(d["reply"], str) or not d["reply"].strip():
            raise SystemExit(f"{f}: empty reply")
        for k in ("logic", "flags"):
            if not isinstance(d[k], list) or not all(isinstance(s, str) for s in d[k]):
                raise SystemExit(f"{f}: '{k}' must be a list of strings")
        found.setdefault(m["item"], {}).setdefault(int(m["round"]), []).append(
            {"model": d["model"].strip(), "reply": d["reply"], "logic": d["logic"], "flags": d["flags"]})
    latest = {}
    for item_id, rounds in found.items():
        n = max(rounds)
        names = [d["model"] for d in rounds[n]]
        if len(names) != len(set(names)):
            raise SystemExit(f"{item_id} round v{n}: two files name the same model {names}")
        latest[item_id] = {"round": n, "drafts": sorted(rounds[n], key=lambda d: d["model"])}
    return latest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("points")
    ap.add_argument("reviews")
    ap.add_argument("style")
    ap.add_argument("out")
    ap.add_argument("--drafts", type=Path)
    a = ap.parse_args()
    try:
        spec, items = load_points(a.points, a.reviews)
    except PointsError as e:
        raise SystemExit(f"{a.points}: {e}") from e
    style = Path(a.style).read_text(encoding="utf-8")
    if not style.strip():
        raise SystemExit(f"{a.style}: empty style file")
    drafts = load_drafts(a.drafts, {it["id"] for it in items}) if a.drafts else {}

    models = sorted({d["model"] for v in drafts.values() for d in v["drafts"]})
    for it in items:
        it["drafts"] = drafts.get(it["id"], {}).get("drafts", [])
    data = {
        "title": spec["title"], "pageId": spec["pageId"], "charLimit": spec["char_limit"], "style": style,
        "models": models, "items": items,
        "reviewers": [{"name": r["name"], "score": r.get("score", "")} for r in spec["reviewers"]],
        "groups": [c["ids"] for c in spec.get("comments", [])],
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    if page.count("/*__DATA__*/null") != 1:
        raise SystemExit(f"{TEMPLATE}: data placeholder not found exactly once")
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    Path(a.out).write_text(page, encoding="utf-8")
    with_drafts = sum(1 for it in items if it["drafts"])
    print(f"wrote {a.out}: {len(items)} items, {with_drafts} with drafts, models {models}, "
          f"{len(data['groups'])} comment groups")


if __name__ == "__main__":
    main()
