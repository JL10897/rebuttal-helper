# OpenReview: how a comment is formatted

Platform rules, the same for every venue that runs on OpenReview. The rules of one venue and year (limits, dates) go in `venues/<conf><year>.md`.

## Text

- Comments render as Markdown with MathJax. A `$` starts inline math and can swallow the text after it; write "USD 5" or "5 dollars", never `$5`. A backslash `\` can trigger LaTeX; avoid it.
- No HTML tags; they are not rendered as intended.
- A single line break does not start a new paragraph. Put a blank line between paragraphs, and before a line that starts with "(ii)" or similar, or it is merged into the paragraph above (`build_submit_page.py` adds that blank line).
- `---` on its own line separates blocks. It needs a blank line above and below: directly under a text line, `---` turns that line into a heading.
- Bold uses `**...**`. The submission page bolds only the "Point n." headings; reply text stays unbolded.

## Tables

- Markdown pipe tables only: a header row, a `|---|` separator row, then body rows.
- No merged cells (no colspan or rowspan). Repeat the value, or split the table in two.
- Keep a table narrow enough to read; very wide tables scroll sideways.

## Subject lines

Each comment has a title field. The submission page fills it as:

- `General Response to All Reviewers` for the General Response, posted on the paper's main thread so all reviewers see it.
- `Response to Reviewer <ID>` when a reviewer gets one comment, using the four-character reviewer ID OpenReview shows.
- `Response to Reviewer <ID> (k/n)` when a reviewer gets several comments, numbered in posting order.

## Posting

- Post a reviewer's comments in order, each as a reply to that reviewer's review, so they read top to bottom.
- Set the readers the venue expects (usually everyone, or reviewers and area chairs); the venue file says which.
