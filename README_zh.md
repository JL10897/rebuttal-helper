# Rebuttal Helper

一个 Claude Code skill：把审稿意见变成可以直接复制、贴到 OpenReview 的回复。

![流程](docs/flow.png)

每一点你写几句笔记，你选的几个模型各写一版草稿，你写定稿。它把定稿分成几条 comment、检查一遍，你自己去发。

```bash
git clone https://github.com/JL10897/rebuttal-helper ~/.claude/skills/rebuttal-helper
```

然后跟 Claude 说：「帮我写 rebuttal，审稿意见在 reviews.html。」 · [详细说明](docs/details.md)
