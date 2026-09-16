import os
import tempfile
import unittest

from pim.controller.commands import run_command
from pim.model.repository import PIRRepository


class AddCommandTests(unittest.TestCase):
    def setUp(self):
        self.repo = PIRRepository()

    def test_add_note_then_print_all_shows_it(self):
        run_command(self.repo, 'add note "buy milk"')
        self.assertIn("buy milk", run_command(self.repo, "print all"))

    def test_add_task_with_iso_deadline(self):
        result = run_command(self.repo, 'add task "finish report" "2026-12-01T10:00:00"')
        self.assertIn("Added", result)

    def test_add_unknown_type_returns_friendly_error(self):
        result = run_command(self.repo, 'add spaceship "nope"')
        self.assertTrue(result.startswith("Error:"))

    def test_add_wrong_argument_count_returns_friendly_error(self):
        result = run_command(self.repo, 'add note')
        self.assertTrue(result.startswith("Error:"))


class EditCommandTests(unittest.TestCase):
    def setUp(self):
        self.repo = PIRRepository()
        run_command(self.repo, 'add note "old text"')

    def test_edit_updates_field(self):
        result = run_command(self.repo, 'edit 1 text="new text"')
        self.assertIn("Updated", result)
        self.assertIn("new text", run_command(self.repo, "print 1"))

    def test_edit_missing_id_returns_friendly_error(self):
        result = run_command(self.repo, 'edit 999 text="new text"')
        self.assertTrue(result.startswith("Error:"))


class PrintDeleteCommandTests(unittest.TestCase):
    def test_delete_then_print_returns_friendly_error(self):
        repo = PIRRepository()
        run_command(repo, 'add note "temp"')
        run_command(repo, "delete 1")
        result = run_command(repo, "print 1")
        self.assertTrue(result.startswith("Error:"))

    def test_print_all_on_empty_repository(self):
        repo = PIRRepository()
        self.assertEqual(run_command(repo, "print all"), "No records found.")


class SearchCommandTests(unittest.TestCase):
    def test_search_returns_only_matching_records(self):
        repo = PIRRepository()
        run_command(repo, 'add note "shopping list"')
        run_command(repo, 'add note "meeting notes"')
        result = run_command(repo, 'search text contains "shopping"')
        self.assertIn("shopping list", result)
        self.assertNotIn("meeting notes", result)

    def test_malformed_search_returns_friendly_error(self):
        repo = PIRRepository()
        result = run_command(repo, "search type = ")
        self.assertTrue(result.startswith("Error:"))


class SaveLoadCommandTests(unittest.TestCase):
    def test_save_then_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "backup")
            repo = PIRRepository()
            run_command(repo, 'add note "persisted note"')
            run_command(repo, f'save "{path}"')

            fresh = PIRRepository()
            result = run_command(fresh, f'load "{path}.pim"')
            self.assertIn("Loaded", result)
            self.assertIn("persisted note", run_command(fresh, "print all"))

    def test_loading_corrupt_next_id_then_adding_does_not_crash(self):
        # Regression test for the crash where a corrupt .pim file with a
        # non-integer next_id loaded "successfully", then the next `add`
        # raised an uncaught TypeError (str + int) inside the repository,
        # killing the REPL. run_command must never raise; it must return a
        # friendly "Error: ..." string instead.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "corrupt.pim")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('{"next_id": "lots", "pirs": []}')

            repo = PIRRepository()
            load_result = run_command(repo, f'load "{path}"')
            self.assertTrue(load_result.startswith("Error:"))

            add_result = run_command(repo, 'add note "x"')
            self.assertTrue(add_result.startswith("Added"))


class MiscCommandTests(unittest.TestCase):
    def test_unknown_command_returns_friendly_error(self):
        result = run_command(PIRRepository(), "fly to the moon")
        self.assertTrue(result.startswith("Error:"))

    def test_help_lists_add_command(self):
        self.assertIn("add note", run_command(PIRRepository(), "help"))

    def test_blank_line_returns_empty_string(self):
        self.assertEqual(run_command(PIRRepository(), "   "), "")


if __name__ == "__main__":
    unittest.main()
