# x-video-downloader

下载公开 X（Twitter）帖子中的最高分辨率 MP4，默认保存到桌面。

## 使用

对 Agent 说：

```text
把这个帖子里的视频下载到桌面：https://x.com/example/status/123
```

也可以直接运行：

```bash
python3 scripts/x_video_downloader.py 'https://x.com/example/status/123'
```

指定目录或覆盖已有文件：

```bash
python3 scripts/x_video_downloader.py '<X 帖子链接>' --output-dir ~/Downloads
python3 scripts/x_video_downloader.py '<X 帖子链接>' --force
```

## 边界

仅处理页面公开暴露的视频资源，不绕过私密内容、付费墙、地区限制或 DRM。请自行确认下载和使用行为符合版权、平台条款与当地法律。
