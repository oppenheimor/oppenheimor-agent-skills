#!/usr/bin/env python3
"""准备 Herdr 雷达的增量窗口，并原子提交各来源游标。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SOURCE_KEYS = (
    "github_releases",
    "official_blog",
    "marketplace",
    "github_community",
    "x_official",
    "x_community",
)
MAX_SEEN_ITEMS = 2000


class StateError(ValueError):
    """状态或运行清单不符合约定。"""


def parse_time(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now().astimezone()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise StateError("时间戳必须包含时区")
    return parsed


def iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def empty_state(created_at: datetime) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": iso(created_at),
        "last_success_at": None,
        "last_report": None,
        "sources": {
            "github_releases": {"last_checked_at": None, "seen_ids": []},
            "official_blog": {"last_checked_at": None, "seen_urls": []},
            "marketplace": {
                "last_checked_at": None,
                "etag": None,
                "generated_at": None,
                "plugins": {},
            },
            "github_community": {
                "last_checked_at": None,
                "seen_repository_ids": [],
            },
            "x_official": {"last_checked_at": None, "seen_post_ids": []},
            "x_community": {"last_checked_at": None, "seen_post_ids": []},
        },
    }


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def validate_state(state: dict[str, Any]) -> None:
    if state.get("schema_version") != SCHEMA_VERSION:
        raise StateError(f"不支持的状态版本：{state.get('schema_version')!r}")
    sources = state.get("sources")
    if not isinstance(sources, dict) or set(sources) != set(SOURCE_KEYS):
        raise StateError("state.json 必须且只能包含六个支持的来源")


def load_or_create_state(root: Path, current: datetime) -> tuple[dict[str, Any], bool]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    state_path = root / "state.json"
    if not state_path.exists():
        state = empty_state(current)
        atomic_write_json(state_path, state)
        return state, True
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StateError(f"无法读取 {state_path}：{error}") from error
    validate_state(state)
    return state, state.get("last_success_at") is None


def bounded_merge(existing: list[Any], incoming: list[Any]) -> list[Any]:
    merged: list[Any] = []
    markers: set[tuple[str, str]] = set()
    for value in [*existing, *incoming]:
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            raise StateError("已读 ID 只能是字符串或整数")
        marker = (type(value).__name__, str(value))
        if marker in markers:
            continue
        markers.add(marker)
        merged.append(value)
    return merged[-MAX_SEEN_ITEMS:]


def source_since(
    state: dict[str, Any],
    source: str,
    current: datetime,
    initial_days: int,
    overlap_days: int,
) -> datetime:
    checked = state["sources"][source].get("last_checked_at")
    if checked:
        return parse_time(checked) - timedelta(days=overlap_days)
    return current - timedelta(days=initial_days)


def command_prepare(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    current = parse_time(args.now)
    state, first_run = load_or_create_state(root, current)
    run_id = current.strftime("%Y-%m-%d-%H%M%S")
    if first_run:
        default_since = current - timedelta(days=args.initial_lookback_days)
    else:
        default_since = parse_time(state["last_success_at"]) - timedelta(
            days=args.overlap_days
        )
    payload = {
        "root": str(root),
        "state_path": str(root / "state.json"),
        "first_run": first_run,
        "window": {"since": iso(default_since), "until": iso(current)},
        "source_windows": {
            source: {
                "since": iso(
                    source_since(
                        state,
                        source,
                        current,
                        args.initial_lookback_days,
                        args.overlap_days,
                    )
                ),
                "until": iso(current),
            }
            for source in SOURCE_KEYS
        },
        "report_path": str(root / "reports" / f"{run_id}.md"),
        "assets_dir": str(root / "assets" / run_id),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def read_manifest(path_value: str) -> dict[str, Any]:
    if path_value == "-":
        raw = sys.stdin.read()
        label = "标准输入"
    else:
        path = Path(path_value).expanduser()
        raw = path.read_text(encoding="utf-8")
        label = str(path)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise StateError(f"{label} 中的运行清单不是有效 JSON：{error}") from error
    if not isinstance(value, dict):
        raise StateError("运行清单必须是 JSON 对象")
    return value


def require_list(update: dict[str, Any], key: str) -> list[Any]:
    value = update.get(key, [])
    if not isinstance(value, list):
        raise StateError(f"{key} 必须是数组")
    return value


def validate_manifest(manifest: dict[str, Any]) -> tuple[datetime, dict[str, Any]]:
    completed_at = manifest.get("completed_at")
    if not isinstance(completed_at, str) or not completed_at.strip():
        raise StateError("运行清单缺少 completed_at")
    completed = parse_time(completed_at)
    sources = manifest.get("sources")
    if not isinstance(sources, dict) or set(sources) != set(SOURCE_KEYS):
        raise StateError("运行清单必须且只能包含六个支持的来源")
    for name, update in sources.items():
        if not isinstance(update, dict):
            raise StateError(f"来源 {name} 必须是对象")
        status = update.get("status")
        if status not in {"ok", "unavailable"}:
            raise StateError(f"来源 {name} 的 status 无效：{status!r}")
        if status == "unavailable":
            reason = update.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise StateError(f"不可用来源 {name} 必须提供 reason")
            unexpected = set(update) - {"status", "reason"}
            if unexpected:
                raise StateError(
                    f"不可用来源 {name} 不能更新游标：{sorted(unexpected)}"
                )
    return completed, sources


def command_commit(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    report = Path(args.report).expanduser().resolve()
    if not report.is_file() or report.stat().st_size == 0:
        raise StateError(f"报告不存在或为空：{report}")
    try:
        report.relative_to(root)
    except ValueError as error:
        raise StateError("报告必须位于雷达数据目录内") from error

    state, _ = load_or_create_state(root, parse_time())
    manifest = read_manifest(args.input)
    completed, updates = validate_manifest(manifest)
    previous_success = state.get("last_success_at")
    if previous_success and completed < parse_time(previous_success):
        raise StateError("completed_at 早于上次成功时间，拒绝回退状态")

    releases = updates["github_releases"]
    if releases["status"] == "ok":
        target = state["sources"]["github_releases"]
        target["last_checked_at"] = iso(completed)
        target["seen_ids"] = bounded_merge(
            target["seen_ids"], require_list(releases, "seen_ids")
        )

    blog = updates["official_blog"]
    if blog["status"] == "ok":
        target = state["sources"]["official_blog"]
        target["last_checked_at"] = iso(completed)
        target["seen_urls"] = bounded_merge(
            target["seen_urls"], require_list(blog, "seen_urls")
        )

    marketplace = updates["marketplace"]
    if marketplace["status"] == "ok":
        target = state["sources"]["marketplace"]
        target["last_checked_at"] = iso(completed)
        if "plugins" in marketplace:
            plugins = marketplace["plugins"]
            if not isinstance(plugins, dict):
                raise StateError("marketplace.plugins 必须是对象")
            target["plugins"] = plugins
        elif not marketplace.get("not_modified"):
            raise StateError("marketplace 成功时必须提供 plugins 或 not_modified")
        if "etag" in marketplace:
            target["etag"] = marketplace["etag"]
        if "generated_at" in marketplace:
            target["generated_at"] = marketplace["generated_at"]

    github = updates["github_community"]
    if github["status"] == "ok":
        target = state["sources"]["github_community"]
        target["last_checked_at"] = iso(completed)
        target["seen_repository_ids"] = bounded_merge(
            target["seen_repository_ids"],
            require_list(github, "seen_repository_ids"),
        )

    for source in ("x_official", "x_community"):
        update = updates[source]
        if update["status"] != "ok":
            continue
        target = state["sources"][source]
        target["last_checked_at"] = iso(completed)
        target["seen_post_ids"] = bounded_merge(
            target["seen_post_ids"], require_list(update, "seen_post_ids")
        )

    state["last_success_at"] = iso(completed)
    state["last_report"] = str(report.relative_to(root))
    state_path = root / "state.json"
    atomic_write_json(state_path, state)
    print(
        json.dumps(
            {
                "committed": True,
                "state_path": str(state_path),
                "last_success_at": state["last_success_at"],
                "last_report": state["last_report"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="创建状态并输出本次运行路径")
    prepare.add_argument("--root", required=True, help="雷达数据目录")
    prepare.add_argument("--initial-lookback-days", type=int, default=14)
    prepare.add_argument("--overlap-days", type=int, default=7)
    prepare.add_argument("--now", help="用于测试的带时区 ISO 时间")
    prepare.set_defaults(handler=command_prepare)

    commit = subparsers.add_parser("commit", help="原子合并一次成功运行")
    commit.add_argument("--root", required=True, help="雷达数据目录")
    commit.add_argument("--report", required=True, help="已完成的报告路径")
    commit.add_argument("--input", default="-", help="运行清单路径，- 表示标准输入")
    commit.set_defaults(handler=command_commit)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "initial_lookback_days", 1) <= 0:
        parser.error("--initial-lookback-days 必须为正数")
    if getattr(args, "overlap_days", 0) < 0:
        parser.error("--overlap-days 不能为负数")
    try:
        return args.handler(args)
    except (OSError, StateError) as error:
        print(f"radar_state：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
