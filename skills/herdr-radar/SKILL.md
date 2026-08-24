---
name: herdr-radar
description: 增量收集 Herdr 的版本发布、官方文章、官方与社区 X 帖子、插件市场和 GitHub 生态项目，生成保留原始链接与媒体、附带简要判断的中文 Markdown 阅读报告。当用户要求了解 Herdr 最新动态、社区新玩法，或刷新自上次运行以来的情报时使用。不要用于控制 Herdr 会话，也不要自动安装、实验或定时运行。
---

# Herdr 雷达

每次由用户手动触发，只生成一份增量阅读报告：

```text
读取上次进度 → 增量收集 → 去重和过滤 → 生成报告 → 提交本次进度
```

默认数据目录为 `~/herdr-radar/`，只包含 `state.json`、`reports/` 和 `assets/`。用户指定其他位置时服从用户选择。

## 边界

- 只在用户要求时运行，不创建定时任务，不主动推送。
- 只收集和分析；不安装插件、不修改 Herdr 配置、不运行社区代码、不自行实验。
- 报告可以提出“以后可考虑尝试什么”，但是否实验由用户决定。
- 不监控 GitHub PR、Issue、Discussion 或官方文档。只有新动态需要解释或核实时，才按需读取相关文档。
- 原始来源是证据。保留直接链接、作者、时间和媒体，不能用搜索结果摘要冒充原文。

## 执行流程

1. 根据当前 `SKILL.md` 的位置解析 Skill 目录，然后准备数据目录并取得增量时间窗口：

   ```bash
   python3 <skill目录>/scripts/radar_state.py prepare --root ~/herdr-radar
   ```

   首次成功运行默认回看 14 天。后续按每个来源上次成功检查的时间向前重叠 7 天，再用稳定 ID 去重。用户指定起始日期时，以用户要求为准。

2. 阅读 [references/sources.md](references/sources.md)。如果环境提供 `web-access` Skill，加载并遵循它；否则使用宿主提供的联网与浏览器工具，并遵循同等的来源验证、登录态隔离和标签页清理规则。六个来源都必须有结果状态：

   - GitHub Releases
   - Herdr 官方 Blog
   - 官方 X `@herdrdev`
   - 社区 X
   - Herdr 插件市场
   - GitHub `herdr` / `herdr-plugin` 社区仓库

   每个来源标记为 `ok` 或 `unavailable`。HTTP 200 但没有出现预期记录，属于失败，不代表“没有更新”。失败来源不得推进游标。

3. 使用稳定身份去重：Release ID、规范文章 URL、仓库 ID 与插件 manifest ID、GitHub Repository ID、X Post ID。插件市场与 `herdr-plugin` Topic 重复时，以插件市场为准。

4. 保留具体的产品变化、新工具或工作流、有实质内容的使用反馈、明确的问题与限制。过滤纯关键词提及、重复转发、低信息回复、营销噪音和已读内容。不做数值评分。

5. 阅读 [references/report-format.md](references/report-format.md)，将报告写入 `prepare` 返回的路径，将媒体放入对应资源目录。报告正文只分为“官方动态”和“社区玩法”两类。

6. 报告完整写入后，创建符合参考文件格式的运行清单，再提交进度：

   ```bash
   python3 <skill目录>/scripts/radar_state.py commit \
     --root ~/herdr-radar \
     --report <报告路径> \
     --input <运行清单.json>
   ```

   `commit` 只合并成功来源的游标，失败来源保持不变，并以原子方式更新状态。报告写入或状态提交失败时，保留旧状态并向用户说明。

7. 关闭本次运行创建的浏览器标签页，不得关闭或操作用户原有标签页。最终告诉用户报告位置、收集时间范围、收录数量和不可用来源。

## 分析标准

每条收录内容只需简洁回答：

1. 发生了什么？
2. 为什么可能值得使用 Herdr 管理 Coding Agent 的用户关注？
3. 用户以后可以考虑尝试什么？

只在有助于扫读时使用 `重要变化`、`有趣玩法`、`暂时观察` 三种轻量标签。明确区分官方事实、社区说法和自己的推断。
