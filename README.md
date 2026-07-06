# Oppenheimor Agent Skills

Personal agent skills, writing workflows, and reusable automation patterns.

这个仓库用于沉淀我自己长期使用的 Agent skills。每个 skill 都放在 `skills/<skill-name>/` 下，保持独立目录结构，方便按名称单独安装。

## 安装

安装单个 skill：

```bash
npx skills add https://github.com/oppenheimor/oppenheimor-agent-skills --skill personal-website-post-writer
```

如果某个 skill 依赖另一个 skill，建议一起安装。例如 `personal-website-post-writer` 会使用 `renhua` 做中文去 AI 味编辑：

```bash
npx skills add https://github.com/oppenheimor/oppenheimor-agent-skills --skill renhua
npx skills add https://github.com/oppenheimor/oppenheimor-agent-skills --skill personal-website-post-writer
```

## Skills

### `personal-website-post-writer`

把当前上下文、部署过程、排障记录、产品体验或 AI 工作流整理成 personal-website 里的中文文章。

它会处理：

- 参考 2026.07 之前的旧文章风格
- 判断文章类型
- 敏感信息脱敏
- 使用 `renhua` 去 AI 味
- 保存到 `src/pages/posts`
- 本地校验
- commit 和 push

### `renhua`

中文 AI/技术写作去 AI 味编辑器。

它主要用于清理这类问题：

- 二元对比壳
- 伪洞察标记
- 冒号讲义腔
- 空泛总结
- 顺滑但没有作者判断的表达

## 仓库结构

```text
oppenheimor-agent-skills/
├── README.md
├── skills.json
├── skills/
│   ├── personal-website-post-writer/
│   │   ├── SKILL.md
│   │   └── evals/
│   │       └── evals.json
│   └── renhua/
│       ├── SKILL.md
│       └── agents/
│           └── openai.yaml
├── templates/
│   └── skill/
│       └── SKILL.md
└── docs/
    └── conventions.md
```

## 新增 skill 约定

每个 skill 使用独立目录：

```text
skills/<skill-name>/
├── SKILL.md
├── references/   # 可选
├── scripts/      # 可选
├── assets/       # 可选
└── evals/        # 可选
```

`SKILL.md` 必须包含 frontmatter：

```yaml
---
name: skill-name
description: 简明描述触发场景和能力边界
---
```

新增或修改 skill 后，同步更新根目录 `skills.json`。

