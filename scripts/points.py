"""Load and validate points.json, the one input of the compare page and the submission page.

The schema is described in SKILL.md (Step 2). load_points() returns the spec plus a flat, ordered
list of items: the General Response (if any), then per reviewer the opening and the numbered points.
Item ids: "general", "<reviewer>-open", "<reviewer>-<n>" (reviewer name in lower case).
"""
import json
import re
from pathlib import Path

SCHEMA = "rebuttal-helper-points/2"
NAME_RE = re.compile(r"[A-Za-z0-9-]+")  # no "_": draft file names use "_" as separator
TOP_KEYS = {"schema", "title", "pageId", "char_limit", "general_response", "reviewers", "comments"}
REVIEWER_KEYS = {"name", "score", "strengths", "points"}
POINT_KEYS = {"title", "paraphrase", "type", "new_result", "quotes"}
POINT_TYPES = {"own_reply", "general_response"}
NEW_RESULT = {"pending", "ready"}
COMMENT_KEYS = {"ids", "note"}


class PointsError(ValueError):
    pass


def norm(s: str) -> str:
    return " ".join(s.split())


def _keys(where, obj, allowed, required):
    if not isinstance(obj, dict):
        raise PointsError(f"{where}: expected an object, got {type(obj).__name__}")
    extra = set(obj) - allowed
    if extra:
        raise PointsError(f"{where}: unknown keys {sorted(extra)} (allowed: {sorted(allowed)})")
    missing = [k for k in required if k not in obj]
    if missing:
        raise PointsError(f"{where}: missing keys {missing}")


def _text(where, value):
    if not isinstance(value, str) or not value.strip():
        raise PointsError(f"{where}: expected a non-empty string, got {value!r:.80}")
    return value


def _quotes(where, quotes, reviews, allow_empty):
    if not isinstance(quotes, list) or (not quotes and not allow_empty):
        raise PointsError(f"{where}: expected a {'' if allow_empty else 'non-empty '}list of excerpts")
    out = []
    for k, q in enumerate(quotes):
        _keys(f"{where}[{k}]", q, {"label", "text"}, ["label", "text"])
        label, text = _text(f"{where}[{k}].label", q["label"]), norm(_text(f"{where}[{k}].text", q["text"]))
        if reviews is not None and text not in reviews:
            raise PointsError(f"{where}[{k}]: excerpt is not verbatim in the reviews text: {text[:90]!r}")
        out.append({"label": label, "text": text})
    return out


def sentences(text: str) -> int:
    return max(1, len(re.findall(r"[.?!](?:\s|$)", text)))


def load_points(points_path, reviews_path=None):
    """Validate points.json. With reviews_path, every excerpt must be verbatim (whitespace-insensitive) in it."""
    points_path = Path(points_path)
    try:
        spec = json.loads(points_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PointsError(f"{points_path}: not valid JSON: {e}") from e
    reviews = norm(Path(reviews_path).read_text(encoding="utf-8")) if reviews_path else None

    _keys("points.json", spec, TOP_KEYS, ["schema", "title", "pageId", "char_limit", "reviewers"])
    if spec["schema"] != SCHEMA:
        raise PointsError(f"points.json: schema must be {SCHEMA!r}, got {spec['schema']!r}")
    _text("title", spec["title"])
    if not isinstance(spec["pageId"], str) or not re.fullmatch(r"[A-Za-z0-9_-]+", spec["pageId"]):
        raise PointsError(f"pageId must be letters/digits/_/-, got {spec['pageId']!r}")
    if not isinstance(spec["char_limit"], int) or spec["char_limit"] <= 0:
        raise PointsError(f"char_limit must be a positive integer (from the venue file), got {spec['char_limit']!r}")
    gr = spec.get("general_response")
    if gr is not None:
        _keys("general_response", gr, {"note"}, [])

    items = []
    if gr is not None:
        items.append({"id": "general", "reviewer": None, "kind": "general", "title": "General Response",
                      "note": gr.get("note", ""), "quotes": []})
    if not isinstance(spec["reviewers"], list) or not spec["reviewers"]:
        raise PointsError("reviewers: expected a non-empty list")
    seen = set()
    for r in spec["reviewers"]:
        _keys(f"reviewer {r.get('name') if isinstance(r, dict) else r!r}", r, REVIEWER_KEYS, ["name", "points"])
        name = r["name"]
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise PointsError(f"reviewer name must be letters/digits/-, got {name!r}")
        if name.lower() in seen:
            raise PointsError(f"duplicate reviewer name {name!r}")
        seen.add(name.lower())
        key = name.lower()
        items.append({"id": f"{key}-open", "reviewer": name, "kind": "opening", "title": "Opening",
                      "quotes": _quotes(f"{name} strengths", r.get("strengths", []), reviews, True)})
        if not isinstance(r["points"], list) or not r["points"]:
            raise PointsError(f"{name}: points must be a non-empty list")
        for n, p in enumerate(r["points"], 1):
            where = f"{name} point {n}"
            _keys(where, p, POINT_KEYS, ["title", "paraphrase", "type", "quotes"])
            if p["type"] not in POINT_TYPES:
                raise PointsError(f"{where}: type must be one of {sorted(POINT_TYPES)}, got {p['type']!r}")
            if p["type"] == "general_response" and gr is None:
                raise PointsError(f"{where}: type is general_response but points.json has no general_response")
            if "new_result" in p and p["new_result"] not in NEW_RESULT:
                raise PointsError(f"{where}: new_result must be one of {sorted(NEW_RESULT)}, got {p['new_result']!r}")
            quotes = _quotes(f"{where} quotes", p["quotes"], reviews, False)
            items.append({"id": f"{key}-{n}", "reviewer": name, "kind": "point", "n": n,
                          "title": _text(f"{where} title", p["title"]),
                          "paraphrase": _text(f"{where} paraphrase", p["paraphrase"]),
                          "type": p["type"], "new_result": p.get("new_result"), "quotes": quotes,
                          "sentences": sum(sentences(q["text"]) for q in quotes)})

    if gr is not None:
        items[0]["quotes"] = [q for it in items if it.get("type") == "general_response" for q in it["quotes"]]
        items[0]["covers"] = [it["id"] for it in items if it.get("type") == "general_response"]

    comments = spec.get("comments")
    if comments is not None:
        _check_comments(comments, items)
    return spec, items


def _check_comments(comments, items):
    order = {it["id"]: k for k, it in enumerate(items)}
    by_id = {it["id"]: it for it in items}
    if not isinstance(comments, list) or not comments:
        raise PointsError("comments: expected a non-empty list")
    used, last = [], {}
    for c, com in enumerate(comments, 1):
        _keys(f"comments[{c}]", com, COMMENT_KEYS, ["ids"])
        ids = com["ids"]
        if not isinstance(ids, list) or not ids:
            raise PointsError(f"comments[{c}]: ids must be a non-empty list")
        unknown = [i for i in ids if i not in by_id]
        if unknown:
            raise PointsError(f"comments[{c}]: unknown item ids {unknown}")
        owners = {by_id[i]["reviewer"] for i in ids}
        if len(owners) != 1:
            raise PointsError(f"comments[{c}]: one comment answers one reviewer (or is the General Response alone), got {ids}")
        who = owners.pop()
        pos = [order[i] for i in ids]
        if pos != sorted(pos) or pos[0] <= last.get(who, -1):
            raise PointsError(f"comments[{c}]: ids out of order {ids}; keep each reviewer's items in point order")
        last[who] = pos[-1]
        used += ids
    repeated = sorted({i for i in used if used.count(i) > 1})
    if repeated:
        raise PointsError(f"comments: ids used more than once {repeated}")
    missing = [it["id"] for it in items if it["kind"] == "point" and it["id"] not in used]
    if missing:
        raise PointsError(f"comments: points not placed in any comment {missing}")
