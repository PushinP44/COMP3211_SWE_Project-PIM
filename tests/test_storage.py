import os
import tempfile
import unittest
from datetime import datetime

from pim.model.errors import StorageError
from pim.model.repository import PIRRepository
from pim.model.storage import load, save


class SaveLoadRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _path(self, name: str) -> str:
        return os.path.join(self.tmpdir.name, name)

    def test_round_trip_preserves_pir_fields(self):
        repo = PIRRepository()
        repo.add("Note", text="buy milk")
        path = save(repo, self._path("data"))

        restored = PIRRepository()
        load(restored, path)
        self.assertEqual(restored.get(1).text, "buy milk")

    def test_round_trip_preserves_next_id_after_delete(self):
        repo = PIRRepository()
        repo.add("Note", text="one")
        second = repo.add("Note", text="two")
        repo.delete(second.id)
        path = save(repo, self._path("data"))

        restored = PIRRepository()
        load(restored, path)
        self.assertEqual(restored.next_id, repo.next_id)
        third = restored.add("Note", text="three")
        self.assertEqual(third.id, 3)

    def test_datetime_fields_round_trip_exactly(self):
        repo = PIRRepository()
        deadline = datetime(2026, 12, 1, 10, 30, 15)
        repo.add("Task", description="finish report", deadline=deadline)
        path = save(repo, self._path("dates"))

        restored = PIRRepository()
        load(restored, path)
        self.assertEqual(restored.get(1).deadline, deadline)

    def test_extension_is_auto_appended(self):
        path = save(PIRRepository(), self._path("no_extension"))
        self.assertTrue(path.endswith(".pim"))
        self.assertTrue(os.path.exists(path))

    def test_conflicting_extension_is_rejected(self):
        with self.assertRaises(StorageError):
            save(PIRRepository(), self._path("data.txt"))

    def test_corrupt_json_raises_storage_error(self):
        path = self._path("broken.pim")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{not valid json")
        with self.assertRaises(StorageError):
            load(PIRRepository(), path)

    def test_missing_file_raises_storage_error(self):
        with self.assertRaises(StorageError):
            load(PIRRepository(), self._path("does_not_exist.pim"))


if __name__ == "__main__":
    unittest.main()
