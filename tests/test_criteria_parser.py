import unittest
from datetime import datetime

from pim.model.criteria_parser import parse_criterion
from pim.model.errors import ParseError
from pim.model.pir import Note, Task


class SimpleComparisonTests(unittest.TestCase):
    def test_contains_comparison(self):
        criterion = parse_criterion('text contains "milk"')
        self.assertTrue(criterion.matches(Note(id=1, text="buy milk")))

    def test_time_comparison(self):
        criterion = parse_criterion('deadline < "2026-07-01T00:00:00"')
        task = Task(id=1, description="x", deadline=datetime(2026, 6, 1))
        self.assertTrue(criterion.matches(task))

    def test_type_equality_comparison(self):
        criterion = parse_criterion('type = "Note"')
        self.assertTrue(criterion.matches(Note(id=1, text="x")))


class PrecedenceTests(unittest.TestCase):
    def test_and_binds_tighter_than_or(self):
        # type="Task" && type="Note" || text contains "x"
        # correct: (type="Task" && type="Note") || (text contains "x") -> False || True -> True
        # wrong:   type="Task" && (type="Note" || text contains "x")   -> False && True  -> False
        note = Note(id=1, text="x")
        criterion = parse_criterion('type="Task" && type="Note" || text contains "x"')
        self.assertTrue(criterion.matches(note))

    def test_not_binds_tighter_than_and(self):
        # !type="Note" && type="Task"
        # correct: (!type="Note") && type="Task" -> False && False -> False
        # wrong:   !(type="Note" && type="Task")  -> !(True && False) -> True
        note = Note(id=1, text="x")
        criterion = parse_criterion('!type="Note" && type="Task"')
        self.assertFalse(criterion.matches(note))

    def test_parentheses_override_precedence(self):
        note = Note(id=1, text="x")
        criterion = parse_criterion('!(type="Task" && type="Note")')
        self.assertTrue(criterion.matches(note))


class QuotingTests(unittest.TestCase):
    def test_operator_characters_inside_quoted_text_are_literal(self):
        criterion = parse_criterion('text contains "cats && dogs"')
        note = Note(id=1, text="I love cats && dogs")
        self.assertTrue(criterion.matches(note))


class ParseErrorTests(unittest.TestCase):
    def test_incomplete_comparison_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse_criterion('type = ')

    def test_unclosed_parenthesis_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse_criterion('(type="Note"')

    def test_invalid_datetime_literal_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse_criterion('deadline < "not-a-date"')

    def test_unexpected_character_raises_parse_error(self):
        with self.assertRaises(ParseError):
            parse_criterion('type @ "Note"')


if __name__ == "__main__":
    unittest.main()
