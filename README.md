# Rebuttal Helper

[English](#english) · [中文](#中文)

## English

You know how to answer your reviewers. The hard part is organizing those answers and saying each one briefly and warmly. Rebuttal Helper is a Claude Code skill that keeps your own thinking at the center.

1. **Split the reviews.** Claude turns the review page into plain text and splits each review into points. A Weakness and a Question about the same issue become one point. You confirm the list.
2. **Jot your notes.** Claude builds a notes page with one box per point. Each box shows the reviewer's exact words (collapsed), how many sentences they used, and a suggested reply length. You write freely, in any language. Boxes autosave.
3. **Get reply drafts.** You submit, and Claude turns each note into a short reply (at most 3 sentences, ideally 2) for you to edit line by line. Each reply opens with sincere, specific thanks, uses simple sentences, and adds no claims you didn't make. Numbers are checked against your PDF, and unfinished results get a visible `[TBD]`.

Claude restates each step before doing it, and never posts anything for you.

### Install

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

Then, in Claude Code: *"Help me write the rebuttal. Reviews are in `reviews.html`, the paper is `paper.pdf`."*

### Where the notes page runs

- **Claude desktop app / claude.ai Code:** published as a private artifact; notes save to the artifact's database, and "Submit to Claude" tells Claude you're done.
- **Anywhere else:** open the HTML file in your browser. Notes are kept in that browser; click "Export JSON for Claude" and hand the file back.

Try it: open `examples/rebuttal_notes_example.html` (built from the toy reviews in `examples/`).

### Tips

- If you have a rebuttal you admire, give it to Claude. It will study how that rebuttal thanks, concedes and clarifies, and vary its phrasing the same way.
- Python 3 standard library only.

---

## 中文

怎么回审稿人，你自己心里有数；难的是把想法理顺，再一条条写得简短、诚恳。Rebuttal Helper 是一个 Claude Code skill，回复的内容始终是你自己的想法。

1. **拆意见**：Claude 把审稿页转成纯文本，按 point 拆分。同一件事的 Weakness 和 Question 合成一条，拆好后给你确认。
2. **写笔记**：Claude 生成一个笔记页，每个 point 一个框。框上方折叠着审稿人的原话，标出原话有几句、建议回几句。你用任何语言随手写，停笔自动保存。
3. **出回复稿**：你点提交后，Claude 把每条笔记整理成一段回复（最多 3 句，最好 2 句），交给你逐句改。开头的致谢具体、真诚，正文用简单句，不加你没说过的结论。数字对照论文 PDF 核对，还没出的结果标 `[TBD]`。

每一步开始前，Claude 都会先复述要做什么。它不会替你在任何地方发布内容。

### 安装

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

然后在 Claude Code 里说：「帮我写 rebuttal，审稿意见在 `reviews.html`，论文是 `paper.pdf`。」

### 笔记页在哪里打开

- **Claude 桌面版 / claude.ai 的 Code**：笔记页发布成私有 artifact，内容存在 artifact 的数据库里。写完点「Submit to Claude」。
- **其他环境**：直接用浏览器打开 HTML 文件，内容存在这个浏览器里。写完点「Export JSON for Claude」，把下载的文件交给 Claude。

想先看看效果，可以打开 `examples/rebuttal_notes_example.html`，它是用 `examples/` 里的示例审稿意见生成的。

### 小提示

- 如果你有一份很喜欢的 rebuttal，可以交给 Claude 参考。它会先看那份 rebuttal 怎么致谢、怎么承认局限、怎么澄清误解，再换着说法写，不会每条都套同一个模板。
- 只依赖 Python 3 标准库。
