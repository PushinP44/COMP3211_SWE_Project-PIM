import unittest
from datetime import datetime

from pim.model.criteria import FieldCriterion
from pim.model.errors import PIRNotFoundError, ValidationError
from pim.model.repository import PIRRepository


class AddTests(unittest.TestCase):
    def test_add_assigns_sequential_ids(self):
        repo = PIRRepository()
        first = repo.add("Note", text="one")
        second = repo.add("Note", text="two")
        self.assertEqual((first.id, second.id), (1, 2))

    def test_add_unknown_type_raises_validation_error(self):
        repo = PIRRepository()
        with self.assertRaises(ValidationError):
            repo.add("Spaceship", text="nope")


class UpdateTests(unittest.TestCase):
    def test_update_changes_field(self):
        repo = PIRRepository()
        note = repo.add("Note", text="old")
        updated = repo.update(note.id, text="new")
        self.assertEqual(updated.text, "new")

    def test_update_advances_modified_at(self):
        repo = PIRRepository()
        note = repo.add("Note", text="old")
        original_modified = note.modified_at
        updated = repo.update(note.id, text="new")
        self.assertGreaterEqual(updated.modified_at, original_modified)

    def test_update_with_invalid_value_leaves_pir_unchanged(self):
        repo = PIRRepository()
        note = repo.add("Note", text="old")
        with self.assertRaises(ValidationError):
            repo.update(note.id, text="   ")
        self.assertEqual(repo.get(note.id).text, "old")

    def test_update_missing_id_raises_not_found(self):
        repo = PIRRepository()
        with self.assertRaises(PIRNotFoundError):
            repo.update(999, text="new")

    def test_update_protected_field_is_rejected(self):
        repo = PIRRepository()
        note = repo.add("Note", text="old")
        with self.assertRaises(ValidationError):
            repo.update(note.id, id=999)


class DeleteTests(unittest.TestCase):
    def test_delete_removes_pir(self):
        repo = PIRRepository()
        note = repo.add("Note", text="temp")
        repo.delete(note.id)
        with self.assertRaises(PIRNotFoundError):
            repo.get(note.id)

    def test_delete_missing_id_raises_not_found(self):
        repo = PIRRepository()
        with self.assertRaises(PIRNotFoundError):
            repo.delete(999)


class NextIdTests(unittest.TestCase):
    def test_id_not_reused_after_deleting_highest_id(self):
        repo = PIRRepository()
        repo.add("Note", text="one")
        second = repo.add("Note", text="two")
        repo.delete(second.id)
        third = repo.add("Note", text="three")
        self.assertEqual(third.id, 3)


class SearchTests(unittest.TestCase):
    def test_search_filters_by_criterion(self):
        repo = PIRRepository()
        repo.add("Note", text="shopping list")
        repo.add("Note", text="meeting notes")
        results = repo.search(FieldCriterion("text", "contains", "shopping"))
        self.assertEqual([r.text for r in results], ["shopping list"])

    def test_search_criterion_on_missing_field_excludes_pir_without_error(self):
        repo = PIRRepository()
        repo.add("Note", text="a note")
        repo.add("Task", description="a task", deadline=datetime(2026, 12, 1))
        results = repo.search(FieldCriterion("deadline", "<", datetime(2027, 1, 1)))
        self.assertEqual([r.description for r in results], ["a task"])


if __name__ == "__main__":
    unittest.main()
