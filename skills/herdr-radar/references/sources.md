# 信息源采集说明

每次执行雷达都要读取本文件。以下路径已在 2026-08-24 实际验证。优先读取一手结构化数据，再打开原始内容补充语境和媒体。

## 通用规则

- 环境提供 `web-access` Skill 时必须遵循它；没有时使用宿主的联网与浏览器能力，并保持相同的来源验证、登录态隔离和标签页清理要求。
- 使用 `radar_state.py prepare` 返回的各来源 `since` 时间。
- 重复拉取重叠窗口，再用稳定 ID 去重，不能只依赖时间戳。
- 只有拿到符合预期结构的记录，来源才算 `ok`。否则写明 `unavailable` 原因，并保留旧游标。
- 搜索引擎只负责发现线索，不能作为事实依据。

## GitHub Releases

首选接口：

```text
https://api.github.com/repos/herdrdev/herdr/releases
```

有登录态时优先使用 `gh api`，否则回退公开 REST API。采集 `id`、`tag_name`、`draft`、`prerelease`、`published_at`、`html_url`、Release Notes 和 Assets。正式版本与有意义的 Preview 都可以收录，但必须明确标注 Preview。

使用数值 Release ID 去重，不能依赖数组位置或只用 Tag。确认响应是包含数值 ID 的数组；公开 API 限额较低，适合时使用认证请求或条件请求。

## 官方 Blog

索引页：

```text
https://herdr.dev/blog/
```

从索引提取规范文章 URL 和 `<time datetime>`。对时间窗口内尚未读过的文章，打开原文并保留标题、日期、原始 URL、代表性媒体和相关外链。正文页面是静态内容，使用 Jina 能明显减少噪音时可以使用。

以规范文章 URL 去重。不要把长文章整篇复制进报告；保留原文链接，用转述和必要的短摘录呈现。

## 插件市场

直接使用官方 JSON：

```text
https://assets.herdr.dev/plugins/index.json
```

确认存在 `schemaVersion`、`generatedAt` 和 `plugins` 数组。响应头存在 `ETag` 时一并保存。仓库记录包含 Repository ID、URL、时间、`headCommit`、`firstSeenAt`、增长数据，以及一个或多个含插件 ID 和版本的 manifest。

以 `(Repository ID, manifest ID)` 为身份，对比 `version`、`headCommit` 和 `firstSeenAt`。报告新插件和有实质意义的升级；普通仓库 Push 但玩法与 manifest 未改变时忽略。紧凑快照格式：

```json
{
  "<repository-id>:<manifest-id>": {
    "version": "1.2.3",
    "head_commit": "abc123",
    "first_seen_at": "..."
  }
}
```

## GitHub 社区仓库

分别搜索两个 Topic：

```text
topic:herdr
topic:herdr-plugin
```

匿名 GitHub Search 限额很低，因此优先使用已认证的 `gh api`。按最近更新时间排序，读取到早于重叠窗口为止。采集 Repository ID、完整名称、URL、描述、Topics、创建时间、更新时间、Push 时间和基础热度信号。

两个集合按 Repository ID 去重。可安装插件以官方插件市场为准；GitHub Topic 主要用于发现非插件客户端、Skill、配置、教程和外围工具，也可作为插件市场异常时的兜底。

## 通过登录态浏览器读取 X

使用 `web-access` 的 CDP 浏览器通道。所有操作在新建后台标签页中完成，并在结束时关闭这些标签页；不得操作或关闭用户原有标签页。

Chrome 可能监听 9222 而非 9333，不能硬编码端口。优先复用已连接的代理；否则读取 Chrome 的 `DevToolsActivePort`，或让代理自行发现。若依赖检查报告端口不符，但 Chrome 远程调试页面明确显示服务已启动，应使用文件中的端口和 Browser WebSocket UUID，不能直接判定 X 不可用。

### 官方 X

打开：

```text
https://x.com/herdrdev
```

只收集 `@herdrdev` 自己发布的帖子，直到最老可见帖早于 `since`。采集 Post ID、作者、精确 `<time datetime>`、Status URL、正文、外链、图片和视频。公开页面可作为后备：从 Profile 提取 Status ID，再通过 X oEmbed 读取文本和日期；优先使用登录态 DOM。

### 社区 X

先执行实时搜索，只有确实带来不同内容时才增加窄查询：

```text
https://x.com/search?q=herdr&src=typed_query&f=live
https://x.com/search?q=%22herdr%20plugin%22&src=typed_query&f=live
https://x.com/search?q=herdr%20filter%3Avideos&src=typed_query&f=live
```

对每个可见 `article` 提取：

- `innerText` 正文
- `<time>` 外层链接中的 Status URL 和 Post ID
- `time.dateTime` 精确时间
- 作者主页链接
- 外部链接
- 图片 URL、视频封面和视频源

持续滚动，直到最老记录早于 `since`、连续两次滚动没有新 Post ID，或已滚动 20 次。不同查询之间按 Post ID 去重。

搜索结果会混入回复和弱相关提及。只保留具体工作流、工具、演示、比较、问题和可信使用反馈；过滤裸推荐、引流内容和无关同名词。

### X 媒体

- 图片：必要时打开帖子 `/photo/N`，取得最大尺寸的 `pbs.twimg.com` 原图，并将合理大小的图片下载到报告资源目录。
- 视频：渲染后的 `<video>` 可能只有 `blob:` URL。此时读取原帖 HTML，提取合适的最高分辨率 `video.twimg.com` MP4，同时保留封面和原帖链接。默认不下载大视频。
- 如果 X 返回空页面、登录墙，或已知有效查询却得到零个 `article`，标记来源不可用，不能解释成“没有更新”。
