---
name: rebuttal-helper
description: Help an author answer peer reviews (OpenReview / conference / journal). Splits the reviews into points, builds a notes page where the author jots their own answer to each point, then turns those notes into short, sincere reply drafts for line-by-line editing. Use when the user says "rebuttal", "respond to reviewers", "author response", "回复审稿人", "写 rebuttal", or shares reviews and asks for help replying.
---

# Rebuttal Helper

The author knows the answers; the hard part is organizing them and saying them briefly and warmly. This skill keeps the author's thinking at the center:

1. split the reviews into points,
2. give the author a notes page with one box per point,
3. turn the submitted notes into reply drafts the author edits line by line.

**Before each step, restate in your own words what you are about to do and wait for the author to confirm.** Rebuttal tone is personal, and a wrong guess costs a round trip.

## What to ask for first

- The reviews: a saved review page (HTML), a PDF, or pasted text.
- The paper: the submitted PDF, and the LaTeX source if available. Treat the paper as read-only.
- A working folder for the rebuttal files. Use the one the author names; otherwise propose `rebuttal/` next to the paper and ask.
- Optional: a rebuttal the author admires (any paper). If given, its style is imitated in Step 4.

## Step 1 — Make one plain-text source of the reviews

All quotes later are checked against this file, so it must contain the reviews word for word.

- HTML page: `python3 <skill>/scripts/html_to_text.py page.html <work>/reviews.txt`. If the script reports almost no text (the page was rendered by JavaScript), ask the author to copy the page text into `reviews.txt` instead.
- PDF: extract the text, or have the author paste it.
- Pasted text: save it as-is.

## Step 2 — Split the reviews into points

Read every review. For each reviewer, collect:

- `score`: one short line with their ratings, if shown.
- `strengths`: the passages where they praise the work (verbatim excerpts). They feed the opening thanks.
- `points`: what needs an answer.
  - Merge a Weakness and a Question about the same issue into one point.
  - Split a paragraph that raises two separate issues.
  - Keep minor typos and presentation nits together in one point.

Give each point a short `title` that says what is being asked, in the author's language, plus the verbatim `quotes` it rests on. Show the author the list (reviewer → point titles) and adjust it until they confirm.

Write `<work>/points.json`:

```json
{
  "title": "Rebuttal Notes: <short paper name>",
  "pageId": "<short-id, used for local storage>",
  "reviewers": [
    {
      "name": "R1",
      "score": "Rating 4 · Confidence 3",
      "strengths": [{"label": "Strength", "text": "<verbatim excerpt>"}],
      "points": [
        {"title": "<what is being asked>",
         "quotes": [{"label": "Weakness", "text": "<verbatim excerpt>"},
                    {"label": "Question", "text": "<verbatim excerpt>"}]}
      ]
    }
  ]
}
```

Use the reviewer IDs the venue shows (e.g. OpenReview's four-character IDs) as `name`; letters, digits, `_` and `-` only.

## Step 3 — Build the notes page

```bash
python3 <skill>/scripts/build_notes_page.py <work>/points.json <work>/reviews.txt <skill>/templates/notes_page.html <work>/rebuttal_notes.html
```

The build fails if any excerpt is not verbatim in `reviews.txt`. Fix the excerpt; never loosen the check.

The page has a General Response box, an opening box per reviewer (their praise shown above it), and one card per point. Each card shows the reviewer's words (collapsed), how many sentences the reviewer used, and a suggested reply length. Boxes autosave. Deliver the page in one of two ways:

- **Claude artifact (Claude desktop app or claude.ai Code).** If you have an Artifact publishing tool, publish `rebuttal_notes.html` as a private artifact. Declare `capabilities: {"db": {"rules": [{"path": "", "read": "admin", "write": "admin"}]}}` so only the author and their editors can read or write the notes. The page saves to the artifact database: collection `notes`, one doc per box (`general`, `<reviewer>-open`, `<reviewer>-<n>`), each `{text, updatedAt}`. "Submit to Claude" writes `meta/submission`.
- **Local file (any other setup).** Tell the author to open `rebuttal_notes.html` in a browser. Notes are kept in that browser. "Export JSON for Claude" downloads `rebuttal_notes_<date>.json` (`{"schema": "rebuttal-helper-notes/1", "notes": {<box id>: text}}`). The author gives that file back to you. "Import JSON" restores a saved export.

Tell the author:
- Write freely, in any language, as rough as they like.
- Aim for replies of at most 3 sentences per point, ideally 2.
- Submit or export when done.

## Step 4 — Turn the notes into reply drafts

Read the notes (artifact database, or the exported JSON). Restate which boxes are filled and which are empty, then draft.

**Content**
- Everything comes from the author's notes. Keep their logic and decisions. Do not add claims, numbers, analyses or promises they did not write.
- Follow instructions the author left inside a note ("shorter", "don't cite the table here", "keep this logic").
- Check numbers, names and section/table/figure labels against the submitted PDF; correct a mismatch and say so.
- If a claim cannot be found in the paper, or the paper contradicts it, keep the reply honest. Soften it or mark `[CHECK: ...]`, and tell the author.
- Results that are still pending get a visible `[TBD: ...]` placeholder, never an invented result.
- A note that only says "see general response" becomes one sentence pointing there.
- An empty note stays empty; list it for the author.

**Length**
- At most 3 sentences per point, ideally 2.
- Go longer only when the reviewer argued at length, or the point truly needs explaining (e.g. positioning against several related works: about 2 sentences per work).
- An opening is 1–2 sentences.

**Voice**
- Simple sentences: one idea per sentence, ordinary words, no stacked clauses or semicolon chains.
- Openings thank the reviewer for something specific, quoting a few of their own words from `strengths`. The thanks must be sincere and concrete, not generic.
- Engage honestly:
  - Say plainly when a point is right ("This is indeed a limitation.").
  - Clear up a misunderstanding without sounding defensive.
  - Say what changed because of the review ("Based on your feedback, we ...") and where in the paper it is.
- Vary the phrasing across points. If the author gave an example rebuttal, first note how it does each of these moves and which small human habits it has (asides in parentheses, an occasional exclamation mark, plain "Yes," starts), then match each point to a fitting move without copying one template.
- Avoid AI tells: "delve", "crucially", "notably", "furthermore/moreover" chains, "robust", "underscore", "it is worth noting", "we would like to emphasize", rule-of-three padding, em-dash overuse, bold text. Don't pile up table/figure citations as proof. Never claim "first" or "only" unless the paper does.

**Output**
- Write `<work>/rebuttal_drafts.md`: General Response first, then each reviewer with their opening and numbered points.
- For each point include the point title, the draft reply, and the author-facing notes (mismatches fixed, claims to check, placeholders).
- Respect the venue's character limit if the author gives one; flag any reply that would exceed it.
- In chat, give only the list of things the author must check or decide.

## Rules

- Never post to OpenReview or any public site, and never email anyone; the author does that.
- Never run new experiments or paid jobs as part of this skill. If a reply needs a new result, leave `[TBD]` and say so.
- Quotes from reviewers stay verbatim.
- Keep all files in the author's working folder, not in temporary directories.
