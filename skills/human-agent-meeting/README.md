# Human-Agent Meeting

![Human-Agent Meeting：人与 Agent 围绕问题讨论并形成决策纪要](./assets/human-agent-meeting-cover.png)

把一段 Human 与 Agent 的往复讨论，当成一场真正的会议。

当讨论告一段落时，显式触发这个 skill。它会回看当前任务中的真实对话，把最终结论、决策依据、被否决的方案、观点转折、未决问题和行动项整理成 Markdown 会议纪要。

它不是聊天记录导出器。纪要以决策为主，同时保留足够的讨论脉络，让未来的自己或另一个 Agent 能够理解：结论是怎样被质疑、修正并最终形成的。

## 适合什么时候用

- 和 Agent 反复讨论一个产品、技术或架构问题后；
- 原始方案经过多轮质疑和修改，最终形成共识时；
- 尚未得到最终答案，但已经排除了一些方向时；
- 想把当前讨论沉淀为项目内可检索的决策资产时；
- 需要给未来接手的 Human 或 Agent 留下可回放的判断过程时。

这个 skill 只接受显式触发。它不会因为某段对话看起来很重要，就擅自替你归档。

## 快速使用

最简单的触发方式：

```text
/human-agent-meeting
```

也可以用自然语言覆盖默认判断：

```text
/human-agent-meeting 话题用“Agent 会议纪要 Skill 设计”
/human-agent-meeting 保存到 ~/notes/meetings
/human-agent-meeting 拆成两份：产品决策、技术实现
```

不需要记忆固定参数。未指定的部分由 Agent 根据当前会议判断。

## 它会记录什么

| 内容 | 处理方式 |
| --- | --- |
| 最终结论 | 放在文档前部，读者无需回放全程就能看到结果 |
| 决策记录 | 记录决定、理由、约束、被否决方案和影响 |
| 关键讨论 | 保留 Human 的质疑、Agent 的修正和共识形成过程 |
| 原始问题 | 保留定义议题的关键原话，必要时脱敏 |
| 未决问题 | 明确标记待验证判断、分歧和阻塞原因 |
| 行动项 | 只记录讨论中明确形成的动作，不虚构负责人或期限 |
| 参考资料 | 只列本次讨论实际使用过的文件、链接、命令和证据 |

它不会逐轮复制聊天，也不会在散会后偷偷追加调查。未经验证的判断会继续保持“待验证”，不会在纪要里摇身一变成为事实。

## 归档规则

会议明确属于某个项目时，写入项目根目录：

```text
<project-root>/docs/meetings/
└── YYYY-MM-DD/
    └── <topic>-会议纪要.md
```

项目归属需要同时满足：存在可识别的项目根目录，并且本次话题确实与这个项目相关。当前目录恰好位于某个 Git 仓库中，不代表这场会属于它。

无法判断项目归属时，skill 会询问保存位置，然后在用户选择的基础目录中创建日期目录：

```text
<user-selected-directory>/
└── YYYY-MM-DD/
    └── <topic>-会议纪要.md
```

同一场会议再次触发时，默认重整并更新原文件，而不是在末尾机械追加。无法确认同名文件是否属于当前会议时，不会静默覆盖。

## 会议状态

即使没有得到完整答案，也可以生成纪要。Frontmatter 使用四种稳定状态：

| 状态 | 含义 |
| --- | --- |
| `concluded` | 已达成结论 |
| `partially_concluded` | 部分达成结论 |
| `unresolved` | 尚未达成结论 |
| `blocked` | 因外部条件阻塞 |

“我们已经确认现在还不知道什么”也是一种有价值的会议结果。

## 默认纪要结构

```markdown
---
date: YYYY-MM-DD
updated: YYYY-MM-DDTHH:mm:ssZ
topic: 具体话题
status: concluded
project: 项目名称或 null
participants:
  - role: Human
  - role: Agent
    tool: Codex
    model: null
tags: []
revision: 1
redacted: false
---

# 具体话题 - 会议纪要

## 会议信息
## 结论摘要
## 议题与目标
### 原始问题
### 最终目标
## 决策记录
## 关键讨论回放
## 未决问题
## 行动项
## 参考资料
```

正文默认跟随会议的主要语言；代码、命令、路径和专有名词保持原样。

## 关键讨论怎样回放

回放的粒度是“观点转折”，不是聊天流水账。例如：

```markdown
### 2. 无项目归属时的保存位置

- Agent 最初建议使用统一的全局目录。
- Human 指出目录不应由 skill 预设，应在实际发生时交给用户决定。
- Agent 接受质疑并修正规则。
- 最终共识：无法判断项目归属时，必须询问用户保存位置。
```

被推翻的观点会明确标记为未采纳，不会和最终结论混在一起。

## 多话题与修订

- 默认围绕一个主要话题生成一份纪要。
- 支线讨论可以被压缩记录，但不会抢占主议题。
- 多个话题各自形成结论时，先询问合并还是拆分。
- 同一会议继续讨论后再次触发，更新原文件并递增 `revision`。
- 后续推翻旧结论时，旧结论移入被否决方案或讨论回放。

## 安全边界

API Key、access token、密码、Cookie、私钥和连接串凭证不会写入纪要。它们会被替换成：

```text
[REDACTED: token]
[REDACTED: password]
```

脱敏会保留问题语义，例如记录“认证因 Token 失效而失败”，但不复制 Token 原值。其他隐私和内部信息不会被无边界地改写，除非用户明确要求。

## 目录结构

```text
human-agent-meeting/
├── README.md
├── SKILL.md
├── assets/
│   ├── human-agent-meeting-cover.png
│   └── meeting-notes-template.md
└── evals/
    └── evals.json
```

- `SKILL.md`：Agent 执行时遵循的完整行为规则；
- `assets/meeting-notes-template.md`：稳定的纪要骨架；
- `evals/evals.json`：项目归属、多话题和修订场景的测试提示。

## 当前边界

- 只整理当前任务中可见的上下文，不跨任务自动拼接历史对话；
- 不负责安装和同步到不同 Agent 工具；
- 不自动提交 Git；
- 不把完整聊天记录当作会议纪要；
- 不在没有用户显式触发时创建文件。
