#!/usr/bin/env python3
"""Download the highest-resolution MP4 videos exposed by a public X post."""

from __future__ import annotations

import argparse
import html as html_module
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

POST_URL_RE = re.compile(
    r"^https?://(?:www\.)?(?:x\.com|twitter\.com)/([^/?#]+)/status/(\d+)(?:[/?#].*)?$",
    re.IGNORECASE,
)
VIDEO_URL_RE = re.compile(
    r"https://video\.twimg\.com/[^\"'<>\\\s]+?\.mp4(?:\?[^\"'<>\\\s]*)?",
    re.IGNORECASE,
)
MEDIA_ID_RE = re.compile(r"/(?:amplify_video|ext_tw_video)/(\d+)/", re.IGNORECASE)
DIMENSIONS_RE = re.compile(r"/(\d+)x(\d+)/")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class VideoVariant:
    media_id: str
    url: str
    width: int
    height: int

    @property
    def pixels(self) -> int:
        return self.width * self.height


def parse_post_url(url: str) -> tuple[str, str]:
    match = POST_URL_RE.match(url.strip())
    if not match:
        raise ValueError("Expected an X post URL such as https://x.com/user/status/123")
    return match.group(1), match.group(2)


def fetch_post_html(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _decode_embedded_url(url: str) -> str:
    return html_module.unescape(url).replace("\\u002F", "/").replace("\\/", "/").replace("\\u0026", "&")


def extract_best_video_urls(page_html: str) -> list[VideoVariant]:
    best_by_media: dict[str, VideoVariant] = {}

    for raw_url in VIDEO_URL_RE.findall(page_html):
        url = _decode_embedded_url(raw_url)
        media_match = MEDIA_ID_RE.search(url)
        dimensions_match = DIMENSIONS_RE.search(url)
        if not media_match or not dimensions_match:
            continue

        width, height = map(int, dimensions_match.groups())
        variant = VideoVariant(media_match.group(1), url, width, height)
        current = best_by_media.get(variant.media_id)
        if current is None or variant.pixels > current.pixels:
            best_by_media[variant.media_id] = variant

    return list(best_by_media.values())


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned or "x"


def build_destination(
    output_dir: Path,
    username: str,
    post_id: str,
    width: int,
    height: int,
    index: int,
    total: int,
) -> Path:
    suffix = f"_{index}" if total > 1 else ""
    filename = (
        f"{_safe_component(username)}_{post_id}_{width}x{height}{suffix}.mp4"
    )
    return output_dir / filename


def download_file(url: str, destination: Path, force: bool = False, timeout: int = 120) -> str:
    if destination.exists() and destination.stat().st_size > 0 and not force:
        return "existing"

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        os.replace(partial, destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise

    return "downloaded"


def download_post_videos(
    post_url: str,
    output_dir: Path,
    force: bool = False,
) -> list[tuple[Path, str]]:
    username, post_id = parse_post_url(post_url)
    page_html = fetch_post_html(post_url)
    videos = extract_best_video_urls(page_html)
    if not videos:
        raise RuntimeError(
            "No public MP4 video was found. The post may contain no video, be private, "
            "require login, or X may have changed its page format."
        )

    results: list[tuple[Path, str]] = []
    for index, video in enumerate(videos, start=1):
        destination = build_destination(
            output_dir,
            username,
            post_id,
            video.width,
            video.height,
            index,
            len(videos),
        )
        status = download_file(video.url, destination, force=force)
        results.append((destination, status))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download the highest-resolution video from a public X post."
    )
    parser.add_argument("url", help="X or Twitter post URL")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / "Desktop",
        help="destination directory (default: ~/Desktop)",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = download_post_videos(args.url, args.output_dir.expanduser(), args.force)
    except (ValueError, RuntimeError, urllib.error.URLError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    for path, status in results:
        label = "Already exists" if status == "existing" else "Downloaded"
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"{label}: {path} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
