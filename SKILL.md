---
name: rebuttal-helper
description: Help an author answer peer reviews (OpenReview / conference / journal), from the review page to copy-ready comments. Splits the reviews into points, settles the reply structure with the author, runs the writing loop on one compare page (author notes, drafts from several models the author picks, the author's finals), then assembles and checks the submission page. Use when the user says "rebuttal", "respond to reviewers", "author response", "回复审稿人", "写 rebuttal", or shares reviews and asks for help replying.
---

# Rebuttal Helper

The author knows the answers. This skill keeps their thinking at the center and gets it into copy-ready comments:

1. **Split** the reviews into points (chat).
2. **Decide the structure** with the author (chat). Output: `points.json`, the one input of both pages.
3. **Writing loop** on the compare page: the author's notes, then drafts from the models the author chose, then the author's final, point by point, as many rounds as needed.
4. **Assemble and check** on the submission page: comments within the venue's limit, subject lines, "Point n." headings, checks.

There are two pages only: the **compare page** (the workbench from notes to finals) and the **submission page** (one copy-ready box per comment).

**Before each step, restate in your own words what you are about to do and wait for the author to confirm.** Rebuttal tone is personal, and a wrong guess costs a round trip.

## Paths

- `<skill>`: this skill's folder.
- `<style>`: `<skill>/style/private/`, the author's private style folder. It is its own git repository, ignored by the public skill repository, and goes with the author from paper to paper. It holds `author_style.md` (the style archive), `references/` (rebuttals the author admires, one file each) and `drafting_models.json` (the models used last time). If it does not exist, create it (`git init`), copy `<skill>/style/author_style.example.md` to `<style>/author_style.md`, and commit there. Commit every change to it there, locally; never push it anywhere.
- `<work>`: the rebuttal's working folder. Use the one the author names; otherwise propose `rebuttal/` next to the paper and ask before creating it. Keep every file here, never in a temporary folder.

## Start: inputs

Ask for, and confirm:

- **The reviews**: a saved review page (HTML), a PDF, or pasted text.
- **The paper as submitted**: the LaTeX source at the submission commit (repository path and commit), or the submitted PDF. Read only.
- **References**: rebuttals the author admires come from `<style>/references/`. Ask whether to add a new one. A new reference is saved as `<style>/references/NN_<short_name>.txt` with a first line giving its source and the date it was added; then write its breakdown (see "Style") and show it to the author before it goes into the archive.
- **Drafting models**: the models that write the drafts. Default: the ones in `<style>/drafting_models.json` (last used). The author may name others, any number. Never assume a model name; after the author confirms, update that file and commit.
- **Venue and year**, e.g. ICLR 2027. Rules change every year, so look them up now (next section).

## Start: this year's venue rules

Search the web for this year's rebuttal rules of the venue, on its official pages. Find:

- the length limit of one comment, and whether a reply can be split over several comments;
- whether a revised PDF can be uploaded, its page limit, and whether changes must be marked;
- the end of the discussion period (with time zone);
- anonymity rules, and whether external links (image hosting, code repositories) are allowed;
- whether new experiments may be added, and any other length or format rules.

Write `<skill>/venues/<conf><year>.md` (e.g. `iclr2027.md`): one row per item with the rule, the source link and the lookup date. An item not found is written as "Not found". Never fill it from an earlier year. Show it to the author; use it only after they confirm. The platform's formatting rules (e.g. `<skill>/venues/openreview.md`) apply on top.

## Step 1 — Split the reviews into points

Make one plain-text source of the reviews. Every quote is checked against it, so it must hold the reviews word for word.

- HTML page: `python3 <skill>/scripts/html_to_text.py page.html <work>/reviews.txt`. If it reports almost no text (the page was rendered by JavaScript), ask the author to copy the page text into `reviews.txt`.
- PDF: extract the text, or have the author paste it. Pasted text: save as is.

Read every review. Per reviewer, collect the score line, the praise (verbatim excerpts, for the opening) and the points:

- merge a Weakness and a Question about the same issue into one point;
- split a paragraph that raises two separate issues;
- keep small typos and presentation nits together in one point.

Each point carries the verbatim excerpts it rests on. Show the list in chat (reviewer → points) and adjust it until the author confirms.

## Step 2 — Decide the structure (with the author, in chat)

Settle with the author:

- which points the General Response answers (shared concerns), which get their own reply, which are merged;
- which points need new results (experiments run outside this skill; the point waits until the result is in);
- for each point, a short title in the author's language, and a one-sentence English paraphrase of what the reviewer asks. The paraphrase becomes the bold "Point n." heading on the submission page, so it must read well to the reviewer.

Do not group comments here; that is Step 4. Write `<work>/points.json`:

```json
{
  "schema": "rebuttal-helper-points/2",
  "title": "Rebuttal: <short paper name>",
  "pageId": "<short-id>",
  "char_limit": 5000,
  "general_response": {"note": "<what it answers, one line>"},
  "reviewers": [
    {
      "name": "Ab12",
      "score": "Rating 4 · Confidence 3",
      "strengths": [{"label": "Strength", "text": "<verbatim excerpt>"}],
      "points": [
        {"title": "<short title, author's language>",
         "paraphrase": "<one English sentence restating the reviewer's question>",
         "type": "own_reply",
         "new_result": "pending",
         "quotes": [{"label": "Weakness", "text": "<verbatim excerpt>"},
                    {"label": "Question", "text": "<verbatim excerpt>"}]}
      ]
    }
  ]
}
```

- `char_limit`: from the confirmed venue file.
- `general_response`: omit when there is none.
- `name`: the reviewer ID the venue shows; letters, digits and `-` only.
- `type`: `own_reply`, or `general_response` when the General Response answers it (the point still gets a one-line reply pointing there).
- `new_result`: only on points that need new results: `pending` until the result is in, then `ready`.
- Item ids follow from the order: `general`, `<name>-open` (the opening), `<name>-<n>` (point n), the name in lower case.

## Step 3 — Writing loop on the compare page

Build:

```bash
python3 <skill>/scripts/build_compare_page.py <work>/points.json <work>/reviews.txt <style>/author_style.md <work>/compare.html [--drafts <work>/drafts]
```

The build stops if an excerpt is not verbatim in `reviews.txt`; fix the excerpt, never loosen the check.

What the page shows:

- **Style box** at the top: the system prompt every drafting model receives. Filled from `author_style.md` until the author edits it; edits are saved in the page's database (collection `style`, doc `system_prompt`).
- **Overview strip**: one row per reviewer, one chip per item: progress (empty → notes → drafts → done), dashed when the General Response answers it, an amber dot while new results are pending, and after Step 4 a band in the colour of its comment.
- **One card per item** in three states: **notes** (reviewer's words collapsed, the title, type tags, a notes box the author writes in any language), **drafts** (one column per model of the latest round, named by the model that wrote it, each with "which sentence carries each point" and notes for the author), **final** (the author's final box and a "Done" tick). After Step 4, each card also shows its comment's live character total.

Deliver the page:

- **Claude artifact** (Claude desktop app or claude.ai Code): publish `compare.html` as a private artifact with `capabilities: {"db": {"rules": [{"path": "", "read": "admin", "write": "admin"}]}}`. The page stores `notes/<item id>` `{text, updatedAt}`, `final/<item id>` `{text, done, updatedAt}`, `style/system_prompt` `{text, updatedAt}`; "Submit to Claude" writes `meta/submission`. After each new round, rebuild and republish to the same artifact; the database stays.
- **Local file** (anywhere else): the author opens `compare.html` in a browser; everything is kept in that browser. "Export JSON for Claude" downloads a file with notes, finals and the style box; "Import JSON" restores one.

The loop, per point:

1. The author writes notes and submits. Read them (artifact database, or the exported JSON) and restate per point which notes you read.
2. Write the brief from `<skill>/templates/brief_template.md`: the author's points in the author's order (the logic is the author's and is not changed), any table to insert as is, the length (set by how much the reviewer wrote and what the point needs; a reply may carry a table; there is no fixed sentence cap), the output format. Save it as `<work>/briefs/<item id>_v<N>.md`.
3. Dispatch each drafting model with the same prompt: the style box text (from the database, or the archive if never edited) as the system prompt, the reference texts (all of them while the library is small; later, the ones the author picks for this round, the rest represented only by their breakdowns in the style box) with the line "Learn the argument flow and tone only; do not copy the wording", then the brief. Each model writes `<work>/drafts/<item id>_v<N>_<model>.json`: `{"model", "reply", "logic", "flags"}`. Claude does not write reply text itself, not even a new sentence or table added to a reply: any new text goes to the models through a brief.
4. Rebuild and republish. The page shows only the latest round of each point; the round number `vN` lives in file names only, to find old drafts and match them to their brief. If the author asks for an older version, find it in the files.
5. The author writes the final in the final box and ticks Done.

**Changing a final.** The author's final is the only source of truth. Claude changes it only by approved minimal fixes: list each proposed fix as its own numbered item (old text → new text, and why); apply an item only after the author quotes it back with "ok". Write to the database pinned to the version you last read (`if_version`); if the author edited it since, the write fails and nothing of theirs is overwritten: re-read and propose again.

### Style: the style box and the archive

- The style box is the system prompt for all drafting models. It has two parts: the rules, and a breakdown of each reference (its argument flow and the moves worth learning; learn the logic and tone, not the wording).
- When the author changes the style box or approves a new habit, list the increments right away, one item each, and classify each:
  - **Special case for this spot**: tied to one reply, one reviewer or one sentence ("call it X in this reply", "do not cite Table 3 here", "add only the table to this point"). It goes into that point's brief or notes only, never into the archive.
  - **General rule**: a habit of tone or structure that would hold for another paper ("do not write 'You are right'", "match the thanks to the score"). It goes into the archive in a general wording, with the original sentence as its example.
  - **Unsure**: when an edit has two readings (e.g. "no 'indeed' here": this sentence only, or the word in general?), list both and let the author choose. Never promote it yourself.
- After the author agrees, write the items into `<style>/author_style.md`, each with its date and source (which paper, which feedback), and commit there.
- When a special case shows up a second time (another point, or another paper), ask the author whether to promote it to a rule.
- A new reference is broken down (how it opens, how a point moves, how it closes, habits worth borrowing, what not to borrow) and shown to the author before the breakdown goes into the archive.

## Step 4 — Assemble and check on the submission page

1. **Dump the finals fresh** from the database: list collection `final` with the output written to `<work>/final_dump_<MMDD>/` (the files land at `final/<item id>.json`). In local mode, unpack the exported JSON into the same layout.
2. **Group into comments.** Run the build without `comments` in `points.json`:
   ```bash
   python3 <skill>/scripts/build_submit_page.py <work>/points.json <work>/final_dump_<MMDD> <work>/submit.html
   ```
   It prints a grouping that fits `char_limit` (each reviewer's items in order, a new comment when the next item would not fit) and stops. Show it to the author; when they confirm or adjust it, add it to `points.json` as `"comments": [{"ids": ["general"], "note": "..."}, {"ids": ["ab12-open", "ab12-1", "ab12-2"]}, ...]`, rebuild the compare page (cards and chips now carry their comment's colour and character total), and run the build again.
3. **Build.** Each comment gets a subject line (`General Response to All Reviewers`, `Response to Reviewer Ab12 (1/2)`), each point a bold `Point n. <paraphrase>` heading (numbered per reviewer, continuing across comments), and a `---` line between blocks with a blank line on both sides. The build **stops** on an empty final, Chinese or full-width characters, a placeholder (`[TBD`, `[CHECK`, `TODO`, `{{`) or HTML, or a comment over the limit. It **prints for the author to confirm one by one**: a reviewer whose last comment has no closing line; replies that cite other works without a References list in their comment; every revision commitment ("have added", "will", "revision", ...). Relay these in chat; do not rewrite anything yourself. A fix goes back through the minimal-fix rule in Step 3.
4. **Check the labels against the paper as submitted:**
   ```bash
   python3 <skill>/scripts/check_labels.py --repo <paper repo> --commit <submission commit> --main main.tex --page <work>/submit.html [--tectonic PATH]
   ```
   It compiles that commit in a temporary folder (never the local build or an old `.aux`), and prints each Appendix / Table / Figure / Section number the replies cite, the reply's words around it, and that number's title or caption in the paper. It fails on a number that does not exist. Show the list; the author checks that each title matches what the reply says. Without LaTeX source, check the numbers against the submitted PDF by hand and say so.
5. **Before the author posts**, dump the finals again, build a fresh page and compare it with the page the author copies from:
   ```bash
   python3 <skill>/scripts/diff_submit_pages.py <work>/submit.html <work>/submit_fresh.html
   ```
   Every comment must be identical. The submission page also marks a box "edited" if the author changed its text locally.
6. Deliver `submit.html` the same way as the compare page (a private artifact, or a local file).

## Rules

- Never post to OpenReview or any public site, and never email anyone; the author does that. Never publish the pages beyond a private artifact.
- Never run new experiments or paid jobs as part of this skill. A point that needs new results stays `pending`; when the author brings the result table, it goes into that point's brief.
- Reviewer quotes stay verbatim; the build checks them.
- Claude does not write reply text. Drafts come from the models the author chose; finals are the author's; Claude applies only approved minimal fixes.
- Round numbers appear only in file names (`briefs/<item id>_v<N>.md`, `drafts/<item id>_v<N>_<model>.json`), never on the pages.
- All files live in `<work>`; style files live in `<style>`.
