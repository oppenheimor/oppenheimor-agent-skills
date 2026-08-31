import io
import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from notchnotes import run  # noqa: E402
from notchnotes_store import NotchNotesPaths, NotchNotesStore  # noqa: E402


class FakeAppController:
    def __init__(self, running=False):
        self.running = running
        self.quit_calls = 0
        self.launch_calls = 0

    def is_running(self):
        return self.running

    def quit(self):
        self.quit_calls += 1
        self.running = False

    def launch(self):
        self.launch_calls += 1
        self.running = True


class NotchNotesCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = NotchNotesPaths(
            notes_file=root / "notes.json",
            preferences_file=root / "preferences.plist",
            backup_root=root / "backups",
            lock_file=root / "write.lock",
        )
        self.store = NotchNotesStore(self.paths, clock=lambda: 300.0)
        self.note_id = "11111111-1111-4111-8111-111111111111"
        self.write_snapshot("- [ ] Existing todo")

    def tearDown(self):
        self.temp.cleanup()

    def write_snapshot(self, text):
        snapshot = {
            "tabs": [{"id": self.note_id, "text": text, "createdAt": 90.0, "selectionLocation": 0, "selectionLength": 0}],
            "activeTabID": self.note_id,
            "savedAt": 100.0,
        }
        self.paths.notes_file.write_text(json.dumps(snapshot), encoding="utf-8")
        self.paths.preferences_file.write_bytes(
            plistlib.dumps({"notchNotes.archive.v2": json.dumps(snapshot).encode()})
        )

    def invoke(self, argv, *, app=None):
        output = io.StringIO()
        code = run(argv, store=self.store, app=app or FakeAppController(), stdout=output)
        return code, json.loads(output.getvalue())

    def test_list_is_read_only_and_returns_json(self):
        app = FakeAppController(running=True)
        code, result = self.invoke(["list"], app=app)
        self.assertEqual(code, 0)
        self.assertEqual(result["notes"][0]["title"], "Existing todo")
        self.assertEqual(app.quit_calls, 0)

    def test_create_reads_markdown_from_file_and_restores_running_app(self):
        content_file = Path(self.temp.name) / "new.md"
        content_file.write_text("- [ ] New todo\n\nExplanation", encoding="utf-8")
        app = FakeAppController(running=True)
        code, result = self.invoke(["create", "--file", str(content_file)], app=app)
        self.assertEqual(code, 0)
        self.assertEqual(result["note"]["title"], "New todo")
        self.assertNotIn("content", result["note"])
        self.assertTrue(result["appRestarted"])
        self.assertEqual((app.quit_calls, app.launch_calls), (1, 1))

    def test_update_reports_revision_conflict_and_restores_running_app(self):
        stale = "sha256:" + "0" * 64
        app = FakeAppController(running=True)
        code, result = self.invoke([
            "update", self.note_id, "--content", "replacement", "--if-revision", stale
        ], app=app)
        self.assertEqual(code, 2)
        self.assertEqual(result["error"]["code"], "REVISION_CONFLICT")
        self.assertEqual((app.quit_calls, app.launch_calls), (1, 1))

    def test_delete_requires_explicit_confirmation(self):
        revision = self.store.read_note(self.note_id)["revision"]
        code, result = self.invoke(["delete", self.note_id, "--if-revision", revision])
        self.assertEqual(code, 2)
        self.assertEqual(result["error"]["code"], "CONFIRMATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
