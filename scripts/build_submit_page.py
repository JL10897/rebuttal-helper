"""Build the submission page: one copy-ready box per comment, with its subject line.

Usage:
    python3 build_submit_page.py points.json DUMP_DIR out.html

DUMP_DIR holds the finals read fresh from the compare page's database: DUMP_DIR/final/<item id>.json,
each {"text": ...} (the layout the artifact database tool writes with out_dir).

Without "comments" in points.json, prints a grouping suggested by char_limit and stops; add the
grouping the author confirms to points.json and run again.

Each comment = its blocks joined by a "---" line: an opening or General Response as written, a point as
a bold "Point n. <paraphrase>" heading plus the final reply. One change is made to the finals: a line
that starts with "(ii) ", "(b) " or "(2) " right under a text line gets a blank line before it, so
Markdown keeps it as its own paragraph.

Stops (exit 1, no page) on: an empty final, Chinese or full-width characters, a placeholder or HTML
tag, a comment over char_limit. Prints for the author to confirm (page is written): reviewers whose
last comment has no closing line, replies that cite other works without a reference list, and every
revision commitment.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from points import PointsError, load_points  # noqa: E402

TEMPLATE = Path(__file__).parent.parent / "templates" / "submit_page.html"
CJK = re.compile(r"[　-〿㐀-䶿一-鿿＀-￯]")
PLACEHOLDER = re.compile(r"\[(?:TBD|CHECK|TODO)\b|\bTODO\b|\bXXX\b|\{\{|<[A-Za-z/!][^>]*>")
ENUM_LINE = re.compile(r"(\S[^\n]*)\n(?=\((?:[ivxlc]+|[a-z]|\d{1,2})\) )")
CITES_WORK = re.compile(r"\bet al\.|\(\d{4}[a-z]?\)|\barXiv\b|\bdoi\.org\b")
HAS_REFERENCES = re.compile(r"^\s*(?:\*\*)?References(?:\*\*)?:?\s*$", re.M | re.I)
# The last sentence of a reviewer's last comment should be a closing line.
CLOSING = re.compile(r"\bthank|\bhappy to\b|\bglad to\b|\blet us know\b|\bfurther questions?\b|\blook forward\b", re.I)
COMMITMENT = re.compile(r"\b(?:have|has) (?:added|updated|revised|included|clarified|moved|fixed|corrected|expanded)\b"
                        r"|\bwill\b|\bwe (?:now|added|updated|revised|include)\b|\brevis(?:ed|ion)\b|\bcamera[- ]ready\b", re.I)


def fail(msg):
    raise SystemExit(f"STOP: {msg}")


def final_text(dump: Path, item_id: str) -> str:
    p = dump / "final" / f"{item_id}.json"
    if not p.is_file():
        fail(f"{p}: no final for {item_id}")
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{p}: not valid JSON: {e}")
    text = d.get("text") if isinstance(d, dict) else None
    if not isinstance(text, str) or not text.strip():
        fail(f"{p}: empty final text")
    text = text.strip()
    if m := CJK.search(text):
        fail(f"{p}: Chinese or full-width character {m.group()!r} at ...{text[max(0, m.start() - 30):m.end() + 10]!r}")
    if m := PLACEHOLDER.search(text):
        fail(f"{p}: placeholder or HTML {m.group()!r} at ...{text[max(0, m.start() - 30):m.end() + 30]!r}")
    return text


def block(item, text):
    return text if item["kind"] != "point" else f"**Point {item['n']}. {item['paraphrase']}**\n\n{text}"


def assemble(ids, by_id, finals):
    return "\n\n---\n\n".join(block(by_id[i], ENUM_LINE.sub(r"\1\n\n", finals[i])) for i in ids)


def suggest(items, by_id, finals, limit):
    """Greedy: per reviewer, in point order, start a new comment when the next item would pass the limit."""
    groups, cur, who = [], [], object()
    for it in items:
        if it["id"] not in finals:
            continue
        if it["reviewer"] != who or it["kind"] == "general" or (cur and len(assemble(cur + [it["id"]], by_id, finals)) > limit):
            if cur:
                groups.append(cur)
            cur, who = [], it["reviewer"]
        cur.append(it["id"])
    groups.append(cur)
    return [{"ids": g} for g in groups]


def label(item):
    return "GR" if item["kind"] == "general" else f"{item['reviewer']} opening" if item["kind"] == "opening" else f"{item['reviewer']}·{item['n']}"


def sentences_of(text):
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+|\n+", text) if s.strip()]


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    points_path, dump, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    try:
        spec, items = load_points(points_path)
    except PointsError as e:
        raise SystemExit(f"{points_path}: {e}") from e
    by_id = {it["id"]: it for it in items}
    limit = spec["char_limit"]

    if "comments" not in spec:
        present = {p.stem for p in (dump / "final").glob("*.json")}
        finals = {it["id"]: final_text(dump, it["id"]) for it in items if it["id"] in present}
        missing = [it["id"] for it in items if it["kind"] == "point" and it["id"] not in finals]
        if missing:
            fail(f"no final for points {missing}")
        print(json.dumps({"comments": suggest(items, by_id, finals, limit)}, indent=2))
        raise SystemExit("points.json has no 'comments'. Above is a grouping suggested by the "
                         f"{limit}-character limit; show it to the author, add the confirmed one to points.json, run again.")

    comments, enum_fixed, finals = [], [], {}
    for c in spec["comments"]:
        ids = c["ids"]
        finals.update({i: final_text(dump, i) for i in ids})
        enum_fixed += [label(by_id[i]) for i in ids if ENUM_LINE.search(finals[i])]
        text = assemble(ids, by_id, finals)
        if len(text) > limit:
            fail(f"comment {ids}: {len(text)} characters, over the {limit} limit")
        who = by_id[ids[0]]["reviewer"]
        pending = [label(by_id[i]) for i in ids if by_id[i].get("new_result") == "pending"]
        comments.append({"who": who or "General Response", "ids": ids, "parts": [label(by_id[i]) for i in ids], "text": text,
                         "note": c.get("note", ""), "pending": f"Waiting for new results: {', '.join(pending)}" if pending else ""})
    changes = [f"A blank line was added before (ii)-style lines in {', '.join(enum_fixed)}, so Markdown keeps them as separate paragraphs."] if enum_fixed else []
    for c in comments:
        same = [x for x in comments if x["who"] == c["who"]]
        if c["who"] == "General Response":
            c["subject"] = "General Response to All Reviewers"
        else:
            c["subject"] = f"Response to Reviewer {c['who']}" + (f" ({same.index(c) + 1}/{len(same)})" if len(same) > 1 else "")

    print("Comments:")
    for k, c in enumerate(comments, 1):
        print(f"  {k}. {c['subject']}: {', '.join(c['parts'])} ({len(c['text'])} / {limit} chars)")

    confirm = []
    for name in [r["name"] for r in spec["reviewers"]]:
        mine = [c for c in comments if c["who"] == name]
        if mine:
            last = sentences_of(mine[-1]["text"])[-1]
            if not CLOSING.search(last):
                confirm.append(f"Closing line: the last comment to {name} ends without one: ...{last[-120:]!r}")
    for c in comments:
        cites = [label(by_id[i]) for i in c["ids"] if CITES_WORK.search(finals[i])]
        if cites and not HAS_REFERENCES.search(c["text"]):
            confirm.append(f"References: {', '.join(cites)} cite other works but \"{c['subject']}\" has no References list")
    commitments = [(label(by_id[i]), s) for c in comments for i in c["ids"]
                   for s in sentences_of(finals[i]) if COMMITMENT.search(s)]
    print("\nConfirm with the author, one by one:")
    for line in confirm:
        print(f"  - {line}")
    if not confirm:
        print("  (no closing-line or reference warnings)")
    print(f"\nRevision commitments ({len(commitments)}), each needs the author's yes:")
    for who, s in commitments:
        print(f"  - [{who}] {s}")

    page = TEMPLATE.read_text(encoding="utf-8")
    for ph in ("/*__DATA__*/null", "/*__META__*/null"):
        if page.count(ph) != 1:
            raise SystemExit(f"{TEMPLATE}: placeholder {ph} not found exactly once")
    data = [{k: c[k] for k in ("who", "subject", "parts", "text", "note", "pending")} for c in comments]
    meta = {"title": spec["title"], "charLimit": limit, "changes": changes}
    page = (page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
                .replace("/*__META__*/null", json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")))
    out.write_text(page, encoding="utf-8")
    print(f"\nwrote {out} ({len(page.encode())} bytes)")


if __name__ == "__main__":
    main()
