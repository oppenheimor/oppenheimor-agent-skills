# 报告与状态提交格式

## 文件结构

`radar_state.py prepare` 会返回准确的报告和资源路径。默认结构：

```text
~/herdr-radar/
|-- state.json
|-- reports/
|   `-- 2026-08-24-103000.md
`-- assets/
    `-- 2026-08-24-103000/
```

资源文件名使用稳定来源 ID，例如 `x-2091685016518705463-1.jpg`。报告中的本地媒体路径通常为 `../assets/<run-id>/文件名`。

## Markdown 报告

```markdown
# Herdr 雷达 — 2026-08-24 10:30

- 收集范围：2026-08-10 10:30 → 2026-08-24 10:30
- 新候选：18 条
- 正文收录：6 条

## 来源健康度

| 来源 | 状态 | 说明 |
|---|---|---|
| GitHub Releases | 正常 | 发现 1 个正式版本 |
| 社区 X | 不可用 | X 登录已失效，游标未推进 |

## 一眼看完

用一小段话概括最值得关注的变化和正在形成的社区玩法。

## 官方动态

### 条目标题

`重要变化`

**原始材料**

- 来源、作者、精确发布时间
- [原始 Release、文章或帖子](https://example.com)
- 必要时附短原文摘录
- 嵌入本地原图，或链接原始视频

**发生了什么**

简洁、可核实的事实说明。

**为什么值得关注**

结合 Herdr 与 Coding Agent 使用场景给出简要判断。

**以后可考虑**

给出一个由用户决定是否进行的实验方向，但不要执行。

## 社区玩法

使用同样的条目结构。

## 采集说明

简要说明不可用来源、过滤限制或尚未核实的社区说法。
```

保持文档适合阅读：

- 使用原始直达 URL，不能使用搜索结果 URL。
- 原文摘录保持简短，长帖和文章用转述表达。
- 明确署名，区分官方事实、社区反馈和自己的推断。
- 图片使用 Markdown 嵌入本地文件。远程视频默认使用封面加原帖链接；稳定 MP4 有必要时可使用 HTML `<video controls>`。
- 如果没有值得关注的新内容，也生成一份简短报告，明确写明结果并保留来源健康度。

## 运行清单

报告完整写入后，创建包含全部六个来源的 JSON。`ok` 来源可以携带游标更新；`unavailable` 来源必须说明原因，且不能携带任何游标数据。

```json
{
  "completed_at": "2026-08-24T10:30:00+08:00",
  "sources": {
    "github_releases": {
      "status": "ok",
      "seen_ids": [373248423]
    },
    "official_blog": {
      "status": "ok",
      "seen_urls": ["https://herdr.dev/blog/example/"]
    },
    "marketplace": {
      "status": "ok",
      "etag": "example",
      "generated_at": "2026-08-24T02:01:22Z",
      "plugins": {
        "123:plugin.example": {
          "version": "1.0.0",
          "head_commit": "abc123",
          "first_seen_at": "2026-08-24T01:00:00Z"
        }
      }
    },
    "github_community": {
      "status": "ok",
      "seen_repository_ids": [123]
    },
    "x_official": {
      "status": "ok",
      "seen_post_ids": ["2090509981346927053"]
    },
    "x_community": {
      "status": "unavailable",
      "reason": "X 登录失效"
    }
  }
}
```

已读列表要包含采集窗口内所有成功观察到的条目，而不只是最终进入报告的条目。否则低价值内容会在每次运行时反复参加海选。
