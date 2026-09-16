import unittest
from datetime import datetime

from pim.model.criteria import AndCriterion, FieldCriterion, NotCriterion, OrCriterion
from pim.model.pir import Note, Task


class FieldCriterionTests(unittest.TestCase):
    def test_contains_matches_case_insensitively(self):
        note = Note(id=1, text="Buy Milk")
        self.assertTrue(FieldCriterion("text", "contains", "milk").matches(note))

    def test_contains_no_match_returns_false(self):
        note = Note(id=1, text="Buy Milk")
        self.assertFalse(FieldCriterion("text", "contains", "eggs").matches(note))

    def test_less_than_operator(self):
        task = Task(id=1, description="x", deadline=datetime(2026, 6, 1))
        self.assertTrue(FieldCriterion("deadline", "<", datetime(2026, 7, 1)).matches(task))

    def test_greater_than_operator(self):
        task = Task(id=1, description="x", deadline=datetime(2026, 6, 1))
        self.assertTrue(FieldCriterion("deadline", ">", datetime(2026, 5, 1)).matches(task))

    def test_equal_operator(self):
        task = Task(id=1, description="x", deadline=datetime(2026, 6, 1))
        self.assertTrue(FieldCriterion("deadline", "=", datetime(2026, 6, 1)).matches(task))

    def test_field_not_present_on_pir_returns_false_not_error(self):
        note = Note(id=1, text="x")
        self.assertFalse(FieldCriterion("deadline", "<", datetime(2026, 1, 1)).matches(note))

    def test_type_field_matches_type_name(self):
        note = Note(id=1, text="x")
        self.assertTrue(FieldCriterion("type", "=", "Note").matches(note))

    def test_type_field_rejects_other_type_name(self):
        note = Note(id=1, text="x")
        self.assertFalse(FieldCriterion("type", "=", "Task").matches(note))


class CompositeCriterionTests(unittest.TestCase):
    def test_and_true_when_both_true(self):
        note = Note(id=1, text="shopping list")
        criterion = AndCriterion(
            FieldCriterion("text", "contains", "shopping"),
            FieldCriterion("type", "=", "Note"),
        )
        self.assertTrue(criterion.matches(note))

    def test_and_false_when_either_false(self):
        note = Note(id=1, text="shopping list")
        criterion = AndCriterion(
            FieldCriterion("text", "contains", "shopping"),
            FieldCriterion("type", "=", "Task"),
        )
        self.assertFalse(criterion.matches(note))

    def test_or_true_when_either_true(self):
        note = Note(id=1, text="shopping list")
        criterion = OrCriterion(
            FieldCriterion("text", "contains", "nonexistent"),
            FieldCriterion("type", "=", "Note"),
        )
        self.assertTrue(criterion.matches(note))

    def test_or_false_when_both_false(self):
        note = Note(id=1, text="shopping list")
        criterion = OrCriterion(
            FieldCriterion("text", "contains", "nonexistent"),
            FieldCriterion("type", "=", "Task"),
        )
        self.assertFalse(criterion.matches(note))

    def test_not_negates_true_to_false(self):
        note = Note(id=1, text="x")
        self.assertFalse(NotCriterion(FieldCriterion("type", "=", "Note")).matches(note))

    def test_not_negates_false_to_true(self):
        note = Note(id=1, text="x")
        self.assertTrue(NotCriterion(FieldCriterion("type", "=", "Task")).matches(note))


if __name__ == "__main__":
    unittest.main()
