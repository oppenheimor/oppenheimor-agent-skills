#!/usr/bin/env python3
"""Safe persistence module for the local NotchNotes archive."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import plistlib
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

APPLE_EPOCH_OFFSET = 978307200.0
DEFAULT_BUNDLE_ID = "io.github.oiloil.NotchNotes"


class NotchNotesError(Exception):
    code = "NOTCHNOTES_ERROR"


class ArchiveNotFound(NotchNotesError):
    code = "ARCHIVE_NOT_FOUND"


class InvalidArchive(NotchNotesError):
    code = "INVALID_ARCHIVE"


class NoteNotFound(NotchNotesError):
    code = "NOTE_NOT_FOUND"


class RevisionConflict(NotchNotesError):
    code = "REVISION_CONFLICT"


class LastNoteDeletionForbidden(NotchNotesError):
    code = "LAST_NOTE_DELETE_FORBIDDEN"


@dataclass(frozen=True)
class NotchNotesPaths:
    notes_file: Path
    preferences_file: Path
    backup_root: Path
    lock_file: Path

    @classmethod
    def for_current_user(cls) -> "NotchNotesPaths":
        home = Path.home()
        state_root = home / "Library" / "Application Support" / "oil-oil-notch-notes"
        return cls(
            notes_file=home / "Library" / "Application Support" / "NotchNotes" / "notes.json",
            preferences_file=home / "Library" / "Preferences" / f"{DEFAULT_BUNDLE_ID}.plist",
            backup_root=state_root / "backups",
            lock_file=state_root / "write.lock",
        )


class NotchNotesStore:
    """Deep module exposing note CRUD while hiding NotchNotes' dual snapshots."""

    def __init__(
        self,
        paths: NotchNotesPaths | None = None,
        *,
        clock: Callable[[], float] | None = None,
        backup_limit: int = 20,
    ) -> None:
        self.paths = paths or NotchNotesPaths.for_current_user()
        self._clock = clock or (lambda: time.time() - APPLE_EPOCH_OFFSET)
        self._backup_limit = backup_limit

    def list_notes(self) -> list[dict]:
        archive = self._load_latest()
        return [self._summary_note(tab) for tab in archive["tabs"]]

    def read_note(self, note_id: str) -> dict:
        archive = self._load_latest()
        return self._public_note(self._find_tab(archive, note_id))

    def create_note(self, content: str) -> dict:
        with self._write_lock():
            archive = self._load_latest_or_empty()
            self._backup()
            now = self._clock()
            note_id = str(uuid.uuid4()).upper()
            tab = {
                "id": note_id,
                "text": content,
                "createdAt": now,
                "selectionLocation": 0,
                "selectionLength": 0,
            }
            archive["tabs"].append(tab)
            archive["activeTabID"] = note_id
            self._save(archive)
            return self._summary_note(tab)

    def update_note(self, note_id: str, content: str, expected_revision: str) -> dict:
        with self._write_lock():
            archive = self._load_latest()
            tab = self._find_tab(archive, note_id)
            self._require_revision(tab, expected_revision)
            self._backup()
            tab["text"] = content
            tab["selectionLocation"] = 0
            tab["selectionLength"] = 0
            archive["activeTabID"] = tab["id"]
            self._save(archive)
            return self._summary_note(tab)

    def delete_note(self, note_id: str, expected_revision: str) -> dict:
        with self._write_lock():
            archive = self._load_latest()
            if len(archive["tabs"]) <= 1:
                raise LastNoteDeletionForbidden("NotchNotes must retain at least one note")
            tab = self._find_tab(archive, note_id)
            self._require_revision(tab, expected_revision)
            self._backup()
            index = archive["tabs"].index(tab)
            archive["tabs"].pop(index)
            if archive["activeTabID"] == tab["id"]:
                archive["activeTabID"] = archive["tabs"][min(index, len(archive["tabs"]) - 1)]["id"]
            self._save(archive)
            return self._summary_note(tab)

    def _load_latest_or_empty(self) -> dict:
        try:
            return self._load_latest()
        except ArchiveNotFound:
            return {"tabs": [], "activeTabID": "", "savedAt": self._clock()}

    def _load_latest(self) -> dict:
        candidates: list[dict] = []
        file_snapshot = self._read_json_snapshot()
        if file_snapshot is not None:
            candidates.append(file_snapshot)
        defaults_snapshot = self._read_defaults_snapshot()
        if defaults_snapshot is not None:
            candidates.append(defaults_snapshot)
        if not candidates:
            if self.paths.notes_file.exists() or self.paths.preferences_file.exists():
                raise InvalidArchive("Neither NotchNotes snapshot is valid")
            raise ArchiveNotFound("No NotchNotes archive exists")
        # Match NoteStore.swift: UserDefaults wins a savedAt tie.
        return max(enumerate(candidates), key=lambda item: (item[1]["savedAt"], item[0]))[1]

    def _read_json_snapshot(self) -> dict | None:
        try:
            value = json.loads(self.paths.notes_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return value if self._is_valid_snapshot(value, allow_empty=False) else None

    def _read_defaults_snapshot(self) -> dict | None:
        try:
            preferences = plistlib.loads(self.paths.preferences_file.read_bytes())
            raw = preferences.get("notchNotes.archive.v2")
            if not isinstance(raw, bytes):
                return None
            value = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError, plistlib.InvalidFileException):
            return None
        return value if self._is_valid_snapshot(value, allow_empty=False) else None

    @staticmethod
    def _is_valid_snapshot(value: object, *, allow_empty: bool) -> bool:
        if not isinstance(value, dict):
            return False
        tabs = value.get("tabs")
        if not isinstance(tabs, list) or (not tabs and not allow_empty):
            return False
        if not isinstance(value.get("savedAt"), (int, float)):
            return False
        active = value.get("activeTabID")
        if not isinstance(active, str):
            return False
        ids: set[str] = set()
        for tab in tabs:
            if not isinstance(tab, dict):
                return False
            try:
                note_id = str(uuid.UUID(str(tab.get("id")))).upper()
            except (ValueError, TypeError, AttributeError):
                return False
            if note_id in ids or not isinstance(tab.get("text"), str):
                return False
            if not isinstance(tab.get("createdAt"), (int, float)):
                return False
            ids.add(note_id)
        return not tabs or active.upper() in ids

    @staticmethod
    def _find_tab(archive: dict, note_id: str) -> dict:
        try:
            canonical = str(uuid.UUID(note_id)).upper()
        except (ValueError, TypeError, AttributeError) as exc:
            raise NoteNotFound(f"Invalid note ID: {note_id}") from exc
        for tab in archive["tabs"]:
            if tab["id"].upper() == canonical:
                return tab
        raise NoteNotFound(f"No note exists with ID {canonical}")

    def _public_note(self, tab: dict) -> dict:
        return {
            "id": tab["id"].upper(),
            "title": self._title(tab["text"]),
            "content": tab["text"],
            "createdAt": tab["createdAt"],
            "revision": self._revision(tab),
        }

    def _summary_note(self, tab: dict) -> dict:
        preview = " ".join(tab["text"].split())
        if len(preview) > 120:
            preview = preview[:119] + "…"
        return {
            "id": tab["id"].upper(),
            "title": self._title(tab["text"]),
            "preview": preview,
            "createdAt": tab["createdAt"],
            "revision": self._revision(tab),
        }

    @staticmethod
    def _title(text: str) -> str:
        title = next((line.strip() for line in text.splitlines() if line.strip()), "")
        prefixes = ("# ", "## ", "### ", "- [ ] ", "- [x] ", "- [X] ", "- ", "* ", "> ")
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
                    changed = True
                    break
        if not title:
            return "Untitled"
        return title if len(title) <= 42 else title[:41] + "…"

    @staticmethod
    def _revision(tab: dict) -> str:
        payload = json.dumps(
            {"id": tab["id"].upper(), "text": tab["text"]},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(payload).hexdigest()

    def _require_revision(self, tab: dict, expected: str) -> None:
        actual = self._revision(tab)
        if expected != actual:
            raise RevisionConflict(f"Note changed since it was read; expected {expected}, current {actual}")

    def _save(self, archive: dict) -> None:
        previous = float(archive.get("savedAt", 0.0))
        archive["savedAt"] = max(self._clock(), previous + 0.001)
        if not self._is_valid_snapshot(archive, allow_empty=False):
            raise InvalidArchive("Mutation produced an invalid NotchNotes archive")
        payload = json.dumps(archive, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        destination = self.paths.notes_file
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".notes.", suffix=".json", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _backup(self) -> None:
        if not self.paths.notes_file.exists() and not self.paths.preferences_file.exists():
            return
        name = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        directory = self.paths.backup_root / name
        directory.mkdir(parents=True, exist_ok=False)
        if self.paths.notes_file.exists():
            shutil.copy2(self.paths.notes_file, directory / "notes.json")
        if self.paths.preferences_file.exists():
            shutil.copy2(self.paths.preferences_file, directory / "preferences.plist")
        backups = sorted((path for path in self.paths.backup_root.iterdir() if path.is_dir()), reverse=True)
        for stale in backups[self._backup_limit:]:
            shutil.rmtree(stale, ignore_errors=True)

    @contextlib.contextmanager
    def _write_lock(self) -> Iterator[None]:
        self.paths.lock_file.parent.mkdir(parents=True, exist_ok=True)
        with self.paths.lock_file.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
