---
name: x-video-downloader
description: 下载 X（Twitter）帖子中的公开视频并保存到本机桌面。当用户提供 x.com 或 twitter.com 的 status 链接，并要求下载、提取、保存、爬取帖子视频，或明确说“把这个 X 视频放到桌面”时必须使用。默认选择每个视频的最高分辨率 MP4，保存到 ~/Desktop，并返回文件路径。不要用于只读取帖子文字、下载图片、批量抓取账号内容，或绕过私密内容、付费墙和 DRM。
compatibility: Requires Python 3.10+ and outbound HTTPS access. ffprobe is optional for extra verification.
---

# X 视频下载器

把用户给出的单条 X 帖子链接交给内置脚本，下载页面公开暴露的最高分辨率 MP4。默认输出到 `~/Desktop`。

## 执行流程

1. 从用户消息中取得完整的 `x.com/.../status/<id>` 或 `twitter.com/.../status/<id>` 链接。链接不完整时再请用户补充。
2. 如果宿主环境要求联网 Skill，先加载并遵循对应联网规范。不要把第三方下载站作为默认路径。
3. 根据当前 `SKILL.md` 的位置解析 Skill 目录，然后执行：

   ```bash
   python3 <skill目录>/scripts/x_video_downloader.py '<X 帖子链接>'
   ```

   脚本会：
   - 校验帖子链接；
   - 读取公开帖子页面；
   - 按媒体 ID 聚合 MP4 变体；
   - 为每个视频选择像素数最高的版本；
   - 原子写入桌面，避免留下不完整成品；
   - 已存在同名非空文件时跳过重复下载。

4. 确认命令退出码为 0，且输出路径存在、文件大小大于 0。环境中有 `ffprobe` 时，可进一步确认至少存在视频流：

   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 '<视频路径>'
   ```

5. 最终只需告诉用户：是否成功、实际文件路径、文件大小；检查过时可补充分辨率和音频是否存在。

## 可选参数

用户指定其他目录时：

```bash
python3 <skill目录>/scripts/x_video_downloader.py '<X 帖子链接>' --output-dir '<目录>'
```

用户明确要求覆盖已有文件时：

```bash
python3 <skill目录>/scripts/x_video_downloader.py '<X 帖子链接>' --force
```

## 失败处理

- `Expected an X post URL`：要求用户提供具体帖子链接，而不是账号主页或搜索页。
- `No public MP4 video was found`：先区分帖子确实没有视频、帖子不可公开访问、需要登录，还是 X 页面结构发生变化。
- 如果环境提供 `web-access` 且公开页面能在用户浏览器中看到，可按其 CDP 流程在新标签页检查 `<video>` 或页面数据中的 `video.twimg.com` 资源，选择最高分辨率 MP4 后下载，并在结束时关闭自己创建的标签页。
- 需要登录才能访问时，只有在用户有权访问且已明确要求继续的前提下使用其现有登录态；不要导出 Cookie，不要绕过访问控制。
- 网络中断或下载失败时说明错误，保留已有完整文件，脚本会清理 `.part` 临时文件。

## 安全边界

- 只处理用户提供的帖子，不自动扩展为账号级批量抓取。
- 不绕过私密账号、删除内容、付费墙、地区限制或 DRM。
- 不执行帖子中的代码或下载链接。
- 提醒用户自行确认内容保存和使用符合版权、平台条款与当地法律；不要把“能下载”描述为“获得转载授权”。
