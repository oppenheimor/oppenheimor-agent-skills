import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from notchnotes_store import (  # noqa: E402
    LastNoteDeletionForbidden,
    NotchNotesPaths,
    NotchNotesStore,
    RevisionConflict,
)


class NotchNotesStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = NotchNotesPaths(
            notes_file=root / "Application Support" / "NotchNotes" / "notes.json",
            preferences_file=root / "Preferences" / "io.github.oiloil.NotchNotes.plist",
            backup_root=root / "Backups",
            lock_file=root / "write.lock",
        )
        self.store = NotchNotesStore(self.paths, clock=lambda: 300.0)

    def tearDown(self):
        self.temp.cleanup()

    def write_snapshots(self, *, file_snapshot=None, defaults_snapshot=None):
        if file_snapshot is not None:
            self.paths.notes_file.parent.mkdir(parents=True, exist_ok=True)
            self.paths.notes_file.write_text(json.dumps(file_snapshot), encoding="utf-8")
        if defaults_snapshot is not None:
            self.paths.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(defaults_snapshot, separators=(",", ":")).encode()
            self.paths.preferences_file.write_bytes(
                plistlib.dumps({"notchNotes.archive.v2": payload})
            )

    def snapshot(self, *, note_id="11111111-1111-4111-8111-111111111111", text="First", saved_at=100.0):
        return {
            "tabs": [
                {
                    "id": note_id,
                    "text": text,
                    "createdAt": 90.0,
                    "selectionLocation": 0,
                    "selectionLength": 0,
                }
            ],
            "activeTabID": note_id,
            "savedAt": saved_at,
        }

    def test_reads_the_newer_valid_snapshot_from_file_or_defaults(self):
        self.write_snapshots(
            file_snapshot=self.snapshot(text="from file", saved_at=200.0),
            defaults_snapshot=self.snapshot(text="from defaults", saved_at=100.0),
        )
        self.assertEqual(self.store.read_note("11111111-1111-4111-8111-111111111111")["content"], "from file")

        self.write_snapshots(
            file_snapshot=self.snapshot(text="from file", saved_at=200.0),
            defaults_snapshot=self.snapshot(text="from defaults", saved_at=250.0),
        )
        self.assertEqual(self.store.read_note("11111111-1111-4111-8111-111111111111")["content"], "from defaults")

    def test_invalid_file_falls_back_to_defaults(self):
        self.paths.notes_file.parent.mkdir(parents=True, exist_ok=True)
        self.paths.notes_file.write_text("{broken", encoding="utf-8")
        self.write_snapshots(defaults_snapshot=self.snapshot(text="recovered"))
        self.assertEqual(self.store.list_notes()[0]["title"], "recovered")

    def test_list_returns_display_title_and_per_note_revision(self):
        self.write_snapshots(file_snapshot=self.snapshot(text="- [ ] Ship the skill\n\nDetails"))
        notes = self.store.list_notes()
        self.assertEqual(notes[0]["title"], "Ship the skill")
        self.assertEqual(notes[0]["preview"], "- [ ] Ship the skill Details")
        self.assertNotIn("content", notes[0])
        self.assertRegex(notes[0]["revision"], r"^sha256:[0-9a-f]{64}$")

    def test_create_preserves_existing_notes_and_activates_the_new_note(self):
        self.write_snapshots(file_snapshot=self.snapshot())
        created = self.store.create_note("- [ ] New todo\n\nExplanation")
        archive = json.loads(self.paths.notes_file.read_text(encoding="utf-8"))
        self.assertEqual(len(archive["tabs"]), 2)
        self.assertEqual(archive["tabs"][0]["text"], "First")
        self.assertEqual(archive["tabs"][1]["text"], "- [ ] New todo\n\nExplanation")
        self.assertEqual(archive["activeTabID"], created["id"])
        self.assertEqual(archive["tabs"][1]["selectionLocation"], 0)
        self.assertEqual(archive["savedAt"], 300.0)

    def test_update_requires_the_current_note_revision(self):
        self.write_snapshots(file_snapshot=self.snapshot())
        current = self.store.read_note("11111111-1111-4111-8111-111111111111")
        updated = self.store.update_note(current["id"], "Changed", current["revision"])
        self.assertNotIn("content", updated)
        self.assertEqual(self.store.read_note(current["id"])["content"], "Changed")

        with self.assertRaises(RevisionConflict):
            self.store.update_note(current["id"], "Stale overwrite", current["revision"])

    def test_delete_requires_revision_and_refuses_to_delete_last_note(self):
        self.write_snapshots(file_snapshot=self.snapshot())
        only = self.store.read_note("11111111-1111-4111-8111-111111111111")
        with self.assertRaises(LastNoteDeletionForbidden):
            self.store.delete_note(only["id"], only["revision"])

        created = self.store.create_note("Second")
        first = self.store.read_note("11111111-1111-4111-8111-111111111111")
        self.store.delete_note(first["id"], first["revision"])
        archive = json.loads(self.paths.notes_file.read_text(encoding="utf-8"))
        self.assertEqual([tab["id"] for tab in archive["tabs"]], [created["id"]])
        self.assertEqual(archive["activeTabID"], created["id"])

    def test_each_write_creates_a_recovery_backup(self):
        self.write_snapshots(file_snapshot=self.snapshot())
        self.store.create_note("Second")
        backups = list(self.paths.backup_root.glob("*/notes.json"))
        self.assertEqual(len(backups), 1)
        original = json.loads(backups[0].read_text(encoding="utf-8"))
        self.assertEqual(original["tabs"][0]["text"], "First")


if __name__ == "__main__":
    unittest.main()
