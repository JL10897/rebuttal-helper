<!--
How the drafting prompt is put together (Claude does this, one prompt per point and round):
  1. the style box text, as the system prompt (read from the compare page's database, collection
     "style", doc "system_prompt"; the archive file if the author never edited the box);
  2. the reference rebuttals the author chose for this round, each under the line
     "Reference rebuttal. Learn its argument flow and tone only; do not copy its wording.";
  3. this brief, filled in.
Save the filled brief as <work>/briefs/<item id>_v<N>.md. Every model gets the same prompt and writes
<work>/drafts/<item id>_v<N>_<model>.json. Fill every {{...}}; delete a section marked (optional)
when it does not apply.
-->
# Brief: {{one line: which reply, e.g. "Reviewer Ab12, point 2: why only two baselines"}}

You are helping the author of a paper submitted to {{venue and year}} with one reply in its rebuttal. Other models get this same brief independently, and the author compares the versions side by side. Work alone; do not ask questions.

## The reviewer's words

{{the verbatim excerpts from points.json, each with its label (Weakness / Question / Strength)}}

## The author's points, in the author's order

Carry every point below, in this order. Do not change the logic: same claims, same order, same numbers, same strength. Do not add arguments, facts, examples, promises or caveats the author did not give, and do not drop any.

1. {{point}}
2. {{point}}

{{Any instruction the author left in their notes ("shorter", "do not cite Table 3 here"), word for word.}}

## Table (optional)

Insert `{{table file}}` exactly as given, with one short line before it saying what it shows, and a blank line on both sides. Do not repeat the table's numbers in the prose.

## Length

{{e.g. "about 200 words of prose, without the table"}}. The whole comment this reply goes into has a hard limit of {{char_limit}} characters, so shorter is better when nothing is lost.

## Format

Plain Markdown that renders on {{platform}}: {{the rules from venues/<platform>.md, e.g. no `$`, no `\`, no HTML, tables with no merged cells}}. ASCII punctuation in the prose.

## Output

Write one JSON file to the path given in your task message:

```json
{"model": "<your model name and version>", "reply": "<the full reply>", "logic": ["for each of the author's points, the sentence of yours that carries it ({{author's language}})"], "flags": ["notes for the author ({{author's language}}): any place where your wording risked changing the meaning, and every revision commitment, as 'Commitment: <sentence>'"]}
```

Validate it with `python3 -c "import json;d=json.load(open(PATH));print(len(d['reply']))"`. Write nothing else. Final message: one line with the word and character count of the reply.
