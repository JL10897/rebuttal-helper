# Rebuttal Helper: details

[English](#english) · [中文](#中文)

## English

You know how to answer your reviewers. The hard part is organizing those answers, saying each one well, and getting every comment out without a slip. Rebuttal Helper is a Claude Code skill that keeps your own thinking at the center, from the review page to copy-ready comments.

1. **Split the reviews.** Claude turns the review page into plain text and splits each review into points. A Weakness and a Question about the same issue become one point. You confirm the list.
2. **Decide the structure together.** In chat, you settle which points the General Response answers, which get their own reply, which need new results, and a one-line restatement of each point that will head its reply.
3. **Write on one page.** The compare page has a card per point. You jot notes in any language; the models you pick each write a draft from your notes and your style rules, shown side by side; you write the final and tick Done. A style box at the top holds your writing rules, and an overview strip shows where every point stands.
4. **Assemble and check.** The submission page splits the finals into comments within the venue's limit, adds subject lines and "Point n." headings, and stops on leftover Chinese, placeholders or a comment over the limit. It lists every revision promise for you to confirm, compiles your paper at the submitted commit to check every Appendix / Table / Figure number the replies cite, and compares the page with a fresh copy of your finals before you post.

Claude restates each step before doing it. It never writes reply text itself, never changes your final without your "ok" on each edit, and never posts anything for you.

### Your style, kept across papers

Your writing rules and the rebuttals you admire live in `style/private/`, a private folder that this repository ignores (make it its own git repository). Every time you change the style box, Claude lists the new rules, asks whether each is a one-off for that reply or a habit worth keeping, and saves the ones you approve, with date and source. Start from `style/author_style.example.md`.

### This year's rules

At the start, Claude looks up this year's rebuttal rules for your venue (comment length, revised PDF, deadline, anonymity and links, new experiments) on the official pages and writes them to `venues/<conf><year>.md` with source links. Anything it cannot find is marked "Not found", never copied from an earlier year. `venues/iclr2027.md` is an example.

### Install

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

Then, in Claude Code: *"Help me write the rebuttal for ICLR 2027. Reviews are in `reviews.html`, the paper source is in `paper/` at commit `abc123`."*

### Where the pages run

- **Claude desktop app / claude.ai Code:** published as private artifacts; notes, finals and the style box save to the artifact's database.
- **Anywhere else:** open the HTML file in a browser. Everything is kept in that browser; "Export JSON for Claude" hands it back.

Try it: open `examples/compare_page_example.html` and `examples/submit_page_example.html`, built from the toy reviews in `examples/`.

### Requirements

Python 3 standard library. The label check needs the paper's LaTeX source with hyperref and [Tectonic](https://tectonic-typesetting.github.io/) (`--tectonic PATH`). Tests: `python3 -m unittest discover -s tests`.

---

## 中文

怎么回审稿人，你自己心里有数；难的是把想法理顺、一条条写好，再一条不错地贴出去。Rebuttal Helper 是一个 Claude Code skill，从审稿页一直走到可以直接复制的回复，内容始终是你自己的想法。

1. **拆意见**：Claude 把审稿页转成纯文本，按点拆分。同一件事的 Weakness 和 Question 合成一点，拆好后给你确认。
2. **一起定结构**：在聊天里定下哪些点由 General Response 回答、哪些单独回、哪些要等新结果，并给每点写一句复述，之后作为这条回复的标题。
3. **在一个页面里写**：对比页每点一张卡片。你用任何语言写笔记；你选的几个模型按你的笔记和你的风格规则各写一版，并排显示；你写定稿、标完成。顶部的风格框存着你的写作规矩，总览条显示每一点走到了哪一步。
4. **组装与检查**：提交页按会议的字数上限把定稿分成几条 comment，加上标题和 "Point n." 小标题；有残留中文、占位符或超长就停下。它会列出所有修订承诺请你确认，编译投稿时那一版论文核对回复里引用的附录、表格、图编号，并在你发之前和重新拉取的定稿逐条比对。

每一步开始前，Claude 都会先复述要做什么。它不自己写回复，不经你逐条说 "ok" 不改你的定稿，也不会替你发布任何内容。

### 你的风格，换论文也带着走

写作规矩和你欣赏的 rebuttal 范例放在 `style/private/`，这个仓库会忽略它（建议单独做成一个 git 仓库）。你每次改风格框，Claude 都会列出新增的规矩，问清每条是只管那一处的特例、还是值得保留的习惯，你同意的才写进存档，并注明日期和来源。可以从 `style/author_style.example.md` 开始。

### 当年的规则

开工时，Claude 会上会议官网查这一届的 rebuttal 规则（每条回复的字数、能否上传修订版 PDF、截止时间、匿名与外链、能否补实验），连同出处链接写进 `venues/<会议><年份>.md`。查不到的项标"Not found"，不沿用往年的值。`venues/iclr2027.md` 是一个例子。

### 安装

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

然后在 Claude Code 里说：「帮我写 ICLR 2027 的 rebuttal，审稿意见在 `reviews.html`，论文源码在 `paper/`，投稿时的 commit 是 `abc123`。」

### 页面在哪里打开

- **Claude 桌面版 / claude.ai 的 Code**：发布成私有 artifact，笔记、定稿和风格框都存在 artifact 的数据库里。
- **其他环境**：直接用浏览器打开 HTML 文件，内容存在这个浏览器里，点「Export JSON for Claude」把文件交给 Claude。

想先看看效果，可以打开 `examples/compare_page_example.html` 和 `examples/submit_page_example.html`，它们是用 `examples/` 里的示例审稿意见生成的。

### 依赖

只依赖 Python 3 标准库。核对编号需要论文的 LaTeX 源码（使用 hyperref）和 [Tectonic](https://tectonic-typesetting.github.io/)（`--tectonic PATH`）。测试：`python3 -m unittest discover -s tests`。
