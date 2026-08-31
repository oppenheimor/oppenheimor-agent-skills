#!/usr/bin/env python3
"""JSON CLI for safe, local NotchNotes note CRUD."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, TextIO

from notchnotes_store import (
    DEFAULT_BUNDLE_ID,
    NoteNotFound,
    NotchNotesError,
    NotchNotesStore,
)


class CliError(NotchNotesError):
    code = "CLI_ERROR"


class ConfirmationRequired(CliError):
    code = "CONFIRMATION_REQUIRED"


class AppQuitTimeout(CliError):
    code = "APP_QUIT_TIMEOUT"


class AppLaunchFailed(CliError):
    code = "APP_LAUNCH_FAILED"


class VerificationFailed(CliError):
    code = "VERIFY_FAILED"


class AppController:
    def __init__(self, *, timeout: float = 8.0) -> None:
        self.timeout = timeout

    def is_running(self) -> bool:
        return subprocess.run(
            ["pgrep", "-x", "NotchNotes"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0

    def quit(self) -> None:
        result = subprocess.run(
            ["osascript", "-e", f'tell application id "{DEFAULT_BUNDLE_ID}" to quit'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            raise AppQuitTimeout("NotchNotes did not accept a normal quit request")
        deadline = time.monotonic() + self.timeout
        while self.is_running() and time.monotonic() < deadline:
            time.sleep(0.1)
        if self.is_running():
            raise AppQuitTimeout("NotchNotes did not quit before the timeout")

    def launch(self) -> None:
        attempts = [["open", "-b", DEFAULT_BUNDLE_ID]]
        home = Path.home()
        attempts.extend(
            [
                ["open", str(home / "Applications" / "NotchNotes.app")],
                ["open", "/Applications/NotchNotes.app"],
                ["open", str(home / "Downloads" / "NotchNotes.app")],
            ]
        )
        for command in attempts:
            if command[0] == "open" and len(command) == 2 and command[1].endswith(".app"):
                if not Path(command[1]).exists():
                    continue
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=self.timeout,
            )
            if result.returncode == 0:
                return
        raise AppLaunchFailed("Unable to locate or launch NotchNotes.app")


class MutationRunner:
    def __init__(self, store: NotchNotesStore, app: AppController) -> None:
        self.store = store
        self.app = app

    def execute(self, operation: Callable[[], dict], verify: Callable[[dict], None]) -> tuple[dict, bool]:
        was_running = self.app.is_running()
        if was_running:
            self.app.quit()
        result: dict | None = None
        operation_error: Exception | None = None
        try:
            result = operation()
        except Exception as exc:
            operation_error = exc
        launch_error: Exception | None = None
        if was_running:
            try:
                self.app.launch()
            except Exception as exc:
                launch_error = exc
        if operation_error is not None:
            raise operation_error
        if launch_error is not None:
            raise launch_error
        assert result is not None
        self._wait_for_verification(lambda: verify(result), wait=was_running)
        return result, was_running

    @staticmethod
    def _wait_for_verification(verify: Callable[[], None], *, wait: bool) -> None:
        deadline = time.monotonic() + (5.0 if wait else 0.0)
        last_error: Exception | None = None
        while True:
            try:
                verify()
                return
            except Exception as exc:
                last_error = exc
            if time.monotonic() >= deadline:
                raise VerificationFailed(f"NotchNotes did not preserve the requested change: {last_error}") from last_error
            time.sleep(0.1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notchnotes", description="Safe local CRUD for NotchNotes notes")
    parser.add_argument("--version", action="version", version="oil-oil-notch-notes 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List notes")
    list_parser.add_argument("--query", help="Filter title and content case-insensitively")

    read_parser = subparsers.add_parser("read", help="Read one note")
    read_parser.add_argument("note_id")

    create_parser = subparsers.add_parser("create", help="Create one note")
    _add_content_source(create_parser)

    update_parser = subparsers.add_parser("update", help="Replace one note's Markdown content")
    update_parser.add_argument("note_id")
    _add_content_source(update_parser)
    update_parser.add_argument("--if-revision", required=True)

    delete_parser = subparsers.add_parser("delete", help="Delete one note")
    delete_parser.add_argument("note_id")
    delete_parser.add_argument("--if-revision", required=True)
    delete_parser.add_argument("--confirmed", action="store_true")
    return parser


def _add_content_source(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Read UTF-8 Markdown from a file; use - for stdin")
    source.add_argument("--content", help="Use the provided Markdown string")


def _read_content(args: argparse.Namespace, stdin: TextIO) -> str:
    if args.content is not None:
        return args.content
    if args.file == "-":
        return stdin.read()
    try:
        return Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CliError(f"Unable to read Markdown file {args.file}: {exc}") from exc


def _emit(stream: TextIO, payload: dict) -> None:
    json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))
    stream.write("\n")


def run(
    argv: list[str] | None = None,
    *,
    store: NotchNotesStore | None = None,
    app: AppController | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = store or NotchNotesStore()
    app = app or AppController()
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    try:
        if args.command == "list":
            notes = store.list_notes()
            if args.query:
                query = args.query.casefold()
                notes = [note for note in notes if query in note["title"].casefold() or query in note["preview"].casefold()]
            _emit(stdout, {"ok": True, "operation": "list", "notes": notes})
            return 0

        if args.command == "read":
            _emit(stdout, {"ok": True, "operation": "read", "note": store.read_note(args.note_id)})
            return 0

        runner = MutationRunner(store, app)
        if args.command == "create":
            content = _read_content(args, stdin)
            note, restarted = runner.execute(
                lambda: store.create_note(content),
                lambda created: _verify_note(store, created["id"], content),
            )
            _emit(stdout, {"ok": True, "operation": "create", "note": note, "appRestarted": restarted})
            return 0

        if args.command == "update":
            content = _read_content(args, stdin)
            note, restarted = runner.execute(
                lambda: store.update_note(args.note_id, content, args.if_revision),
                lambda updated: _verify_note(store, updated["id"], content),
            )
            _emit(stdout, {"ok": True, "operation": "update", "note": note, "appRestarted": restarted})
            return 0

        if args.command == "delete":
            if not args.confirmed:
                raise ConfirmationRequired("Delete requires --confirmed after explicit user confirmation")
            deleted, restarted = runner.execute(
                lambda: store.delete_note(args.note_id, args.if_revision),
                lambda removed: _verify_deleted(store, removed["id"]),
            )
            _emit(stdout, {"ok": True, "operation": "delete", "deletedNote": deleted, "appRestarted": restarted})
            return 0

        raise CliError(f"Unknown command: {args.command}")
    except NotchNotesError as exc:
        _emit(stdout, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})
        return 2
    except Exception as exc:
        _emit(stdout, {"ok": False, "error": {"code": "UNEXPECTED_ERROR", "message": str(exc)}})
        return 1


def _verify_note(store: NotchNotesStore, note_id: str, expected_content: str) -> None:
    actual = store.read_note(note_id)
    if actual["content"] != expected_content:
        raise VerificationFailed("Saved note content differs from the requested content")


def _verify_deleted(store: NotchNotesStore, note_id: str) -> None:
    try:
        store.read_note(note_id)
    except NoteNotFound:
        return
    raise VerificationFailed("Deleted note is still present")


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
