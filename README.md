# Rebuttal Helper

A Claude Code skill for writing a rebuttal. It does not give you ideas: AI cannot think about your paper deeply enough to argue it well. What it takes off your hands is everything else, so you only think about the logic.

![How it works](docs/flow.png)

**You** decide how to answer each point, in a few notes, in any language.

**It** splits the reviews into points with the reviewer's exact words, has the models you pick turn your notes into drafts side by side, keeps notes, drafts and finals on one page, formats the finals into OpenReview comments under the length limit, and checks them for leftover Chinese, placeholders, and table or appendix numbers that do not match your paper. You post them yourself.

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

Then tell Claude: "Help me write the rebuttal. The reviews are in reviews.html." · [中文](README_zh.md)
