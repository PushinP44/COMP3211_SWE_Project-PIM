import unittest

from pim.model.errors import ValidationError
from pim.model.pir import Contact, Note, PIR_REGISTRY


class NoteTests(unittest.TestCase):
    def test_valid_note_stores_text(self):
        note = Note(id=1, text="buy milk")
        self.assertEqual(note.text, "buy milk")

    def test_blank_text_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Note(id=1, text="   ")

    def test_field_value_returns_text(self):
        note = Note(id=1, text="buy milk")
        self.assertEqual(note.field_value("text"), "buy milk")

    def test_field_value_unknown_field_raises_key_error(self):
        note = Note(id=1, text="buy milk")
        with self.assertRaises(KeyError):
            note.field_value("deadline")

    def test_round_trips_through_to_dict_and_from_dict(self):
        note = Note(id=1, text="buy milk")
        restored = Note.from_dict(note.to_dict())
        self.assertEqual(restored.id, note.id)
        self.assertEqual(restored.text, note.text)
        self.assertEqual(restored.created_at, note.created_at)


class ContactTests(unittest.TestCase):
    def test_valid_contact_stores_fields(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        self.assertEqual(contact.name, "Alice")
        self.assertEqual(contact.address, "1 Main St")
        self.assertEqual(contact.mobile_number, "98765432")

    def test_blank_mobile_number_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Contact(id=1, name="Alice", address="1 Main St", mobile_number="")

    def test_round_trips_through_to_dict_and_from_dict(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        restored = Contact.from_dict(contact.to_dict())
        self.assertEqual(restored.name, contact.name)
        self.assertEqual(restored.mobile_number, contact.mobile_number)


class RegistryTests(unittest.TestCase):
    def test_note_and_contact_are_registered(self):
        self.assertIs(PIR_REGISTRY["Note"], Note)
        self.assertIs(PIR_REGISTRY["Contact"], Contact)


if __name__ == "__main__":
    unittest.main()
