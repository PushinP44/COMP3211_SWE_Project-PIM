import unittest
from datetime import datetime, timedelta

from pim.model.errors import ValidationError
from pim.model.pir import Contact, Event, Note, PIR_REGISTRY, Task


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

    def test_field_value_returns_name(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        self.assertEqual(contact.field_value("name"), "Alice")

    def test_field_value_returns_address(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        self.assertEqual(contact.field_value("address"), "1 Main St")

    def test_field_value_returns_mobile_number(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        self.assertEqual(contact.field_value("mobile_number"), "98765432")

    def test_field_value_unknown_field_raises_key_error(self):
        contact = Contact(id=1, name="Alice", address="1 Main St", mobile_number="98765432")
        with self.assertRaises(KeyError):
            contact.field_value("deadline")


class TaskTests(unittest.TestCase):
    def test_valid_task_stores_fields(self):
        deadline = datetime(2026, 12, 1, 10, 0)
        task = Task(id=1, description="finish report", deadline=deadline)
        self.assertEqual(task.description, "finish report")
        self.assertEqual(task.deadline, deadline)

    def test_non_datetime_deadline_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Task(id=1, description="finish report", deadline="not a date")

    def test_blank_description_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Task(id=1, description="   ", deadline=datetime(2026, 12, 1, 10, 0))

    def test_round_trips_datetime_through_to_dict_and_from_dict(self):
        deadline = datetime(2026, 12, 1, 10, 0)
        task = Task(id=1, description="finish report", deadline=deadline)
        restored = Task.from_dict(task.to_dict())
        self.assertEqual(restored.deadline, deadline)

    def test_field_value_returns_description(self):
        task = Task(id=1, description="finish report", deadline=datetime(2026, 12, 1, 10, 0))
        self.assertEqual(task.field_value("description"), "finish report")

    def test_field_value_returns_deadline(self):
        deadline = datetime(2026, 12, 1, 10, 0)
        task = Task(id=1, description="finish report", deadline=deadline)
        self.assertEqual(task.field_value("deadline"), deadline)

    def test_field_value_unknown_field_raises_key_error(self):
        task = Task(id=1, description="finish report", deadline=datetime(2026, 12, 1, 10, 0))
        with self.assertRaises(KeyError):
            task.field_value("text")


class EventTests(unittest.TestCase):
    def test_alarm_before_start_time_is_valid(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start - timedelta(minutes=10)
        event = Event(id=1, description="meeting", start_time=start, alarm=alarm)
        self.assertEqual(event.alarm, alarm)

    def test_alarm_equal_to_start_time_is_valid(self):
        start = datetime(2026, 12, 1, 10, 0)
        event = Event(id=1, description="meeting", start_time=start, alarm=start)
        self.assertEqual(event.alarm, start)

    def test_alarm_after_start_time_raises_validation_error(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start + timedelta(minutes=5)
        with self.assertRaises(ValidationError):
            Event(id=1, description="meeting", start_time=start, alarm=alarm)

    def test_blank_description_raises_validation_error(self):
        start = datetime(2026, 12, 1, 10, 0)
        with self.assertRaises(ValidationError):
            Event(id=1, description="   ", start_time=start, alarm=start)

    def test_non_datetime_start_time_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Event(id=1, description="meeting", start_time="not a date", alarm="not a date")

    def test_non_datetime_alarm_raises_validation_error(self):
        start = datetime(2026, 12, 1, 10, 0)
        with self.assertRaises(ValidationError):
            Event(id=1, description="meeting", start_time=start, alarm="not a date")

    def test_field_value_returns_description(self):
        start = datetime(2026, 12, 1, 10, 0)
        event = Event(id=1, description="meeting", start_time=start, alarm=start)
        self.assertEqual(event.field_value("description"), "meeting")

    def test_round_trips_datetime_through_to_dict_and_from_dict(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start - timedelta(minutes=10)
        event = Event(id=1, description="meeting", start_time=start, alarm=alarm)
        restored = Event.from_dict(event.to_dict())
        self.assertEqual(restored.start_time, start)
        self.assertEqual(restored.alarm, alarm)

    def test_field_value_returns_start_time(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start - timedelta(minutes=10)
        event = Event(id=1, description="meeting", start_time=start, alarm=alarm)
        self.assertEqual(event.field_value("start_time"), start)

    def test_field_value_returns_alarm(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start - timedelta(minutes=10)
        event = Event(id=1, description="meeting", start_time=start, alarm=alarm)
        self.assertEqual(event.field_value("alarm"), alarm)

    def test_field_value_unknown_field_raises_key_error(self):
        start = datetime(2026, 12, 1, 10, 0)
        alarm = start - timedelta(minutes=10)
        event = Event(id=1, description="meeting", start_time=start, alarm=alarm)
        with self.assertRaises(KeyError):
            event.field_value("text")


class RegistryTests(unittest.TestCase):
    def test_all_four_pir_types_are_registered(self):
        self.assertEqual(set(PIR_REGISTRY.keys()), {"Note", "Task", "Event", "Contact"})


if __name__ == "__main__":
    unittest.main()
