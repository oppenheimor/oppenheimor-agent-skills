# Skill 编写约定

## 命名

- 目录名和 frontmatter `name` 保持一致。
- 使用小写英文和连字符，例如 `personal-website-post-writer`。
- 不使用 `my-skill`、`test-skill` 这类临时名字。

## 目录

每个 skill 放在：

```text
skills/<skill-name>/
```

标准结构：

```text
skills/<skill-name>/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── evals/
```

除 `SKILL.md` 外，其余目录按需创建。

## SKILL.md

frontmatter 至少包含：

```yaml
---
name: skill-name
description: >
  触发场景 + 能力范围 + 默认产出。
---
```

正文应该说明：

- 什么时候使用
- 默认流程
- 输入来源
- 输出位置或格式
- 校验方式
- 安全边界

## 触发描述

`description` 是最重要的触发入口。写得太泛会误触发，写得太窄会漏触发。

推荐包含：

- 用户可能说出的关键词
- 任务类型
- 明确的产出
- 需要避免的边界

## 依赖

如果一个 skill 依赖另一个 skill：

- 在 README 的安装示例中写清楚。
- 在 `SKILL.md` 中说明 fallback。
- 尽量不要只写死本机绝对路径。

## 测试

主观写作类 skill 可以先保留轻量测试提示：

```text
evals/evals.json
```

固定流程类、文件生成类、代码修改类 skill 后续再补断言。

