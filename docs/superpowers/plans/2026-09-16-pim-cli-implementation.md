# PIM CLI System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the command-line PIM system (all 11 user stories) plus its full model-layer unit test suite, exactly as designed in the spec.

**Architecture:** MVC adapted for a CLI. `pim/model/` holds all domain logic (PIR types, search-criterion tree + parser, in-memory repository, JSON persistence) and is the only package the assignment requires unit tests for. `pim/controller/` splits raw REPL input and dispatches to the model. `pim/view/` formats output. `pim/main.py` wires it together into a REPL loop.

**Tech Stack:** Python 3.11+, standard library only at runtime (`abc`, `dataclasses`-free plain classes, `datetime`, `json`, `re`, `shlex`, `pathlib`). Tests use `unittest` (stdlib). Coverage reporting uses `coverage.py` (dev-time only, not imported by shipped code).

**Spec:** `docs/superpowers/specs/2026-09-15-pim-cli-system-design.md`

## Global Constraints

- Python, object-oriented (spec §1).
- Implementation imports only the Python standard library at runtime (spec §7); `coverage.py` is dev-only tooling and exempt.
- All domain/model code lives under `pim/model/`, including the criterion-grammar parser — moved there specifically so it falls under the assignment's required unit-test scope (spec §2 correction).
- Datetime fields serialize via `.isoformat()` and deserialize via `datetime.fromisoformat()` (spec §5) — never hand a raw `datetime` to `json.dump`.
- `.pim` extension is auto-appended if missing on `save`/`load`, and a conflicting extension is rejected (spec §5).
- Search's `contains` operator is case-insensitive (spec §4).
- A search criterion naming a field a given PIR type doesn't have evaluates to `False`, never raises (spec §4).
- `Event.alarm` must be `<= start_time` (spec §3).
- One test method per behavior, named after the behavior — no broad multi-assertion tests (spec §8).
- No malformed input or corrupt `.pim` file may crash the program — always a caught, friendly error message (spec §6).

---

### Task 1: Project scaffolding and error hierarchy

**Files:**
- Create: `pim/__init__.py`, `pim/model/__init__.py`, `pim/controller/__init__.py`, `pim/view/__init__.py`
- Create: `pim/model/errors.py`
- Create: `tests/__init__.py`, `tests/test_errors.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `pim.model.errors.{PimError, ValidationError, PIRNotFoundError, ParseError, StorageError}` — every later task raises/catches these exact names.

- [ ] **Step 1: Create package `__init__.py` files (all empty)**

```bash
mkdir -p pim/model pim/controller pim/view tests
touch pim/__init__.py pim/model/__init__.py pim/controller/__init__.py pim/view/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_errors.py`:

```python
import unittest

from pim.model.errors import (
    ParseError,
    PimError,
    PIRNotFoundError,
    StorageError,
    ValidationError,
)


class ErrorHierarchyTests(unittest.TestCase):
    def test_validation_error_is_a_pim_error(self):
        self.assertTrue(issubclass(ValidationError, PimError))

    def test_pir_not_found_error_is_a_pim_error(self):
        self.assertTrue(issubclass(PIRNotFoundError, PimError))

    def test_parse_error_is_a_pim_error(self):
        self.assertTrue(issubclass(ParseError, PimError))

    def test_storage_error_is_a_pim_error(self):
        self.assertTrue(issubclass(StorageError, PimError))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_errors -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.errors'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/errors.py`:

```python
class PimError(Exception):
    """Base class for all PIM domain errors."""


class ValidationError(PimError):
    """Raised when a PIR's field values fail validation."""


class PIRNotFoundError(PimError):
    """Raised when an operation references an id that doesn't exist."""


class ParseError(PimError):
    """Raised when a search-criterion expression can't be parsed."""


class StorageError(PimError):
    """Raised when a .pim file can't be saved or loaded."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_errors -v`
Expected: 4 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim tests
git commit -m "feat: scaffold pim package and error hierarchy"
```

---

### Task 2: PIR base class, registry, `Note`, `Contact`

**Files:**
- Create: `pim/model/pir.py`
- Test: `tests/test_pir.py`

**Interfaces:**
- Consumes: `pim.model.errors.ValidationError` (Task 1).
- Produces: `PIR` (abstract base with `id`, `created_at`, `modified_at`, `validate()`, `field_value(field) -> Any`, `to_dict() -> dict`, `PIR.from_dict(dict) -> PIR`, `touch()`), `PIR_REGISTRY: dict[str, type[PIR]]`, `register_pir(type_name)` decorator, `Note(id, text, **kwargs)`, `Contact(id, name, address, mobile_number, **kwargs)`. Task 3 adds `Task`/`Event` to the same file and registry.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pir.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_pir -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.pir'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/pir.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar

from pim.model.errors import ValidationError

PIR_REGISTRY: dict[str, type["PIR"]] = {}


def register_pir(type_name: str):
    """Class decorator: registers a PIR subclass under `type_name` and sets
    its `type_name` class attribute. Adding a 5th PIR type only needs this
    decorator on the new class — no other file changes (design spec §3)."""

    def decorator(cls: type["PIR"]) -> type["PIR"]:
        PIR_REGISTRY[type_name] = cls
        cls.type_name = type_name
        return cls

    return decorator


class PIR(ABC):
    """Abstract base for all Personal Information Records."""

    type_name: ClassVar[str] = "pir"

    def __init__(
        self,
        id: int,
        created_at: datetime | None = None,
        modified_at: datetime | None = None,
    ) -> None:
        self.id = id
        now = datetime.now()
        self.created_at = created_at or now
        self.modified_at = modified_at or now

    @abstractmethod
    def validate(self) -> None:
        """Raise ValidationError if this PIR's current field values are invalid."""

    @abstractmethod
    def field_value(self, field: str) -> Any:
        """Return the value of `field`. Raise KeyError if this PIR type
        doesn't have that field — model/criteria.py treats that as 'this
        record can't match a criterion on this field', not as an error."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict, including a 'type' tag."""

    @classmethod
    def from_dict(cls, data: dict) -> "PIR":
        pir_cls = PIR_REGISTRY[data["type"]]
        return pir_cls._from_dict(data)

    @classmethod
    @abstractmethod
    def _from_dict(cls, data: dict) -> "PIR":
        """Subclass hook: reconstruct an instance from a dict produced by to_dict()."""

    def touch(self) -> None:
        self.modified_at = datetime.now()

    def _base_dict(self) -> dict:
        return {
            "type": self.type_name,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    @staticmethod
    def _base_kwargs(data: dict) -> dict:
        return {
            "id": data["id"],
            "created_at": datetime.fromisoformat(data["created_at"]),
            "modified_at": datetime.fromisoformat(data["modified_at"]),
        }


@register_pir("Note")
class Note(PIR):
    def __init__(self, id: int, text: str, **kwargs) -> None:
        super().__init__(id, **kwargs)
        self.text = text
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValidationError("Note.text must be a non-empty string")

    def field_value(self, field: str):
        if field == "text":
            return self.text
        raise KeyError(field)

    def to_dict(self) -> dict:
        data = self._base_dict()
        data["text"] = self.text
        return data

    @classmethod
    def _from_dict(cls, data: dict) -> "Note":
        return cls(text=data["text"], **cls._base_kwargs(data))


@register_pir("Contact")
class Contact(PIR):
    def __init__(self, id: int, name: str, address: str, mobile_number: str, **kwargs) -> None:
        super().__init__(id, **kwargs)
        self.name = name
        self.address = address
        self.mobile_number = mobile_number
        self.validate()

    def validate(self) -> None:
        for field_name in ("name", "address", "mobile_number"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"Contact.{field_name} must be a non-empty string")

    def field_value(self, field: str):
        if field in ("name", "address", "mobile_number"):
            return getattr(self, field)
        raise KeyError(field)

    def to_dict(self) -> dict:
        data = self._base_dict()
        data.update(name=self.name, address=self.address, mobile_number=self.mobile_number)
        return data

    @classmethod
    def _from_dict(cls, data: dict) -> "Contact":
        return cls(
            name=data["name"],
            address=data["address"],
            mobile_number=data["mobile_number"],
            **cls._base_kwargs(data),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_pir -v`
Expected: 7 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/pir.py tests/test_pir.py
git commit -m "feat: add PIR base class, registry, Note, Contact"
```

---

### Task 3: `Task` and `Event` PIR types

**Files:**
- Modify: `pim/model/pir.py` (append `Task`, `Event`)
- Modify: `tests/test_pir.py` (append `TaskTests`, `EventTests`; extend `RegistryTests`)

**Interfaces:**
- Consumes: `PIR`, `register_pir`, `PIR_REGISTRY`, `ValidationError` (Task 2).
- Produces: `Task(id, description, deadline, **kwargs)`, `Event(id, description, start_time, alarm, **kwargs)`, both registered in `PIR_REGISTRY`. `Task 5` (repository) and `Task 6` (parser) rely on the field names `description`, `deadline`, `start_time`, `alarm` exactly.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_pir.py` (add these imports to the existing `from pim.model.pir import ...` line: `Event, Task`; add `from datetime import datetime, timedelta` at the top):

```python
class TaskTests(unittest.TestCase):
    def test_valid_task_stores_fields(self):
        deadline = datetime(2026, 12, 1, 10, 0)
        task = Task(id=1, description="finish report", deadline=deadline)
        self.assertEqual(task.description, "finish report")
        self.assertEqual(task.deadline, deadline)

    def test_non_datetime_deadline_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Task(id=1, description="finish report", deadline="not a date")

    def test_round_trips_datetime_through_to_dict_and_from_dict(self):
        deadline = datetime(2026, 12, 1, 10, 0)
        task = Task(id=1, description="finish report", deadline=deadline)
        restored = Task.from_dict(task.to_dict())
        self.assertEqual(restored.deadline, deadline)


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
```

Replace the existing `RegistryTests` class body with:

```python
class RegistryTests(unittest.TestCase):
    def test_all_four_pir_types_are_registered(self):
        self.assertEqual(set(PIR_REGISTRY.keys()), {"Note", "Task", "Event", "Contact"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_pir -v`
Expected: FAIL — `ImportError: cannot import name 'Task' from 'pim.model.pir'`

- [ ] **Step 3: Write minimal implementation**

Append to `pim/model/pir.py`:

```python
@register_pir("Task")
class Task(PIR):
    def __init__(self, id: int, description: str, deadline: datetime, **kwargs) -> None:
        super().__init__(id, **kwargs)
        self.description = description
        self.deadline = deadline
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValidationError("Task.description must be a non-empty string")
        if not isinstance(self.deadline, datetime):
            raise ValidationError("Task.deadline must be a datetime")

    def field_value(self, field: str):
        if field == "description":
            return self.description
        if field == "deadline":
            return self.deadline
        raise KeyError(field)

    def to_dict(self) -> dict:
        data = self._base_dict()
        data.update(description=self.description, deadline=self.deadline.isoformat())
        return data

    @classmethod
    def _from_dict(cls, data: dict) -> "Task":
        return cls(
            description=data["description"],
            deadline=datetime.fromisoformat(data["deadline"]),
            **cls._base_kwargs(data),
        )


@register_pir("Event")
class Event(PIR):
    def __init__(
        self, id: int, description: str, start_time: datetime, alarm: datetime, **kwargs
    ) -> None:
        super().__init__(id, **kwargs)
        self.description = description
        self.start_time = start_time
        self.alarm = alarm
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValidationError("Event.description must be a non-empty string")
        if not isinstance(self.start_time, datetime):
            raise ValidationError("Event.start_time must be a datetime")
        if not isinstance(self.alarm, datetime):
            raise ValidationError("Event.alarm must be a datetime")
        if self.alarm > self.start_time:
            raise ValidationError("Event.alarm must be at or before start_time")

    def field_value(self, field: str):
        if field == "description":
            return self.description
        if field == "start_time":
            return self.start_time
        if field == "alarm":
            return self.alarm
        raise KeyError(field)

    def to_dict(self) -> dict:
        data = self._base_dict()
        data.update(
            description=self.description,
            start_time=self.start_time.isoformat(),
            alarm=self.alarm.isoformat(),
        )
        return data

    @classmethod
    def _from_dict(cls, data: dict) -> "Event":
        return cls(
            description=data["description"],
            start_time=datetime.fromisoformat(data["start_time"]),
            alarm=datetime.fromisoformat(data["alarm"]),
            **cls._base_kwargs(data),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_pir -v`
Expected: 14 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/pir.py tests/test_pir.py
git commit -m "feat: add Task and Event PIR types"
```

---

### Task 4: Search-criterion classes (`criteria.py`)

**Files:**
- Create: `pim/model/criteria.py`
- Test: `tests/test_criteria.py`

**Interfaces:**
- Consumes: `PIR`, `Note`, `Task` (Tasks 2-3, tests only — `criteria.py` itself only depends on the `field_value`/`type_name` interface, not concrete PIR classes).
- Produces: `Criterion` (interface with `matches(pir) -> bool`), `FieldCriterion(field, op, value)`, `AndCriterion(left, right)`, `OrCriterion(left, right)`, `NotCriterion(operand)`. Task 5 (repository) and Task 6 (parser) build/consume these exact names.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_criteria.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_criteria -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.criteria'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/criteria.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pim.model.pir import PIR

_CONTAINS = "contains"


class Criterion(ABC):
    @abstractmethod
    def matches(self, pir: PIR) -> bool:
        ...


class FieldCriterion(Criterion):
    """Leaf criterion: `field <op> value`. See design spec §4 for the
    canonical field/operator table."""

    def __init__(self, field: str, op: str, value) -> None:
        self.field = field
        self.op = op
        self.value = value

    def matches(self, pir: PIR) -> bool:
        if self.field == "type":
            return self.op == "=" and pir.type_name == self.value

        try:
            actual = pir.field_value(self.field)
        except KeyError:
            return False

        if self.op == _CONTAINS:
            if not isinstance(actual, str):
                return False
            return self.value.lower() in actual.lower()

        if not isinstance(actual, datetime):
            return False
        if self.op == "<":
            return actual < self.value
        if self.op == ">":
            return actual > self.value
        if self.op == "=":
            return actual == self.value
        raise ValueError(f"Unknown operator '{self.op}'")


class AndCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self.left = left
        self.right = right

    def matches(self, pir: PIR) -> bool:
        return self.left.matches(pir) and self.right.matches(pir)


class OrCriterion(Criterion):
    def __init__(self, left: Criterion, right: Criterion) -> None:
        self.left = left
        self.right = right

    def matches(self, pir: PIR) -> bool:
        return self.left.matches(pir) or self.right.matches(pir)


class NotCriterion(Criterion):
    def __init__(self, operand: Criterion) -> None:
        self.operand = operand

    def matches(self, pir: PIR) -> bool:
        return not self.operand.matches(pir)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_criteria -v`
Expected: 14 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/criteria.py tests/test_criteria.py
git commit -m "feat: add Criterion classes for search (US7)"
```

---

### Task 5: `PIRRepository`

**Files:**
- Create: `pim/model/repository.py`
- Test: `tests/test_repository.py`

**Interfaces:**
- Consumes: `PIR`, `PIR_REGISTRY` (Task 2/3), `Criterion`, `FieldCriterion` (Task 4), `ValidationError`, `PIRNotFoundError` (Task 1).
- Produces: `PIRRepository()` with `.add(pir_type: str, **fields) -> PIR`, `.get(id: int) -> PIR`, `.get_all() -> list[PIR]`, `.update(id: int, **fields) -> PIR`, `.delete(id: int) -> None`, `.search(criterion: Criterion) -> list[PIR]`, `.next_id -> int` (property), `.load_snapshot(pirs: Iterable[PIR], next_id: int) -> None`. Task 7 (storage) and Task 8 (commands) call these exact names.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_repository.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_repository -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.repository'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/repository.py`:

```python
from __future__ import annotations

from typing import Iterable

from pim.model.criteria import Criterion
from pim.model.errors import PIRNotFoundError, ValidationError
from pim.model.pir import PIR, PIR_REGISTRY

_PROTECTED_FIELDS = {"id", "created_at", "modified_at", "type_name"}


class PIRRepository:
    def __init__(self) -> None:
        self._pirs: dict[int, PIR] = {}
        self._next_id = 1

    @property
    def next_id(self) -> int:
        return self._next_id

    def add(self, pir_type: str, **fields) -> PIR:
        try:
            pir_cls = PIR_REGISTRY[pir_type]
        except KeyError:
            raise ValidationError(f"Unknown PIR type '{pir_type}'") from None
        pir = pir_cls(id=self._next_id, **fields)
        self._pirs[pir.id] = pir
        self._next_id += 1
        return pir

    def get(self, id: int) -> PIR:
        try:
            return self._pirs[id]
        except KeyError:
            raise PIRNotFoundError(f"No PIR with id {id}") from None

    def get_all(self) -> list[PIR]:
        return list(self._pirs.values())

    def update(self, id: int, **fields) -> PIR:
        pir = self.get(id)
        for field_name in fields:
            if field_name in _PROTECTED_FIELDS:
                raise ValidationError(f"'{field_name}' cannot be edited")
            if not hasattr(pir, field_name):
                raise ValidationError(f"{pir.type_name} has no field '{field_name}'")

        original = dict(pir.__dict__)
        for field_name, value in fields.items():
            setattr(pir, field_name, value)
        try:
            pir.validate()
        except Exception:
            pir.__dict__.clear()
            pir.__dict__.update(original)
            raise
        pir.touch()
        return pir

    def delete(self, id: int) -> None:
        if id not in self._pirs:
            raise PIRNotFoundError(f"No PIR with id {id}")
        del self._pirs[id]

    def search(self, criterion: Criterion) -> list[PIR]:
        return [pir for pir in self._pirs.values() if criterion.matches(pir)]

    def load_snapshot(self, pirs: Iterable[PIR], next_id: int) -> None:
        """Replace repository contents wholesale — used by storage.load."""
        self._pirs = {pir.id: pir for pir in pirs}
        self._next_id = next_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_repository -v`
Expected: 11 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/repository.py tests/test_repository.py
git commit -m "feat: add PIRRepository (US1, US6, US7, US9)"
```

---

### Task 6: Search-criterion parser (`criteria_parser.py`)

**Files:**
- Create: `pim/model/criteria_parser.py`
- Test: `tests/test_criteria_parser.py`

**Interfaces:**
- Consumes: `Criterion`, `FieldCriterion`, `AndCriterion`, `OrCriterion`, `NotCriterion` (Task 4), `ParseError` (Task 1).
- Produces: `parse_criterion(text: str) -> Criterion`. Task 8 (`commands.py`, `handle_search`) calls this exact function.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_criteria_parser.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_criteria_parser -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.criteria_parser'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/criteria_parser.py`:

```python
from __future__ import annotations

import re
from datetime import datetime

from pim.model.criteria import AndCriterion, Criterion, FieldCriterion, NotCriterion, OrCriterion
from pim.model.errors import ParseError

_TIME_FIELDS = {"deadline", "start_time", "alarm"}

_TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<STRING>"(?:[^"\\]|\\.)*")
      | (?P<AND>&&)
      | (?P<OR>\|\|)
      | (?P<NOT>!)
      | (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<EQ>=)
      | (?P<LT><)
      | (?P<GT>>)
      | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    )""",
    re.VERBOSE,
)


def _unquote(token: str) -> str:
    return token[1:-1].replace('\\"', '"').replace("\\\\", "\\")


def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if not match or match.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ParseError(f"Unexpected character at position {pos}: {text[pos]!r}")
        pos = match.end()
        kind = match.lastgroup
        tokens.append((kind, match.group(kind)))
    return tokens


class _CriterionParser:
    """Recursive-descent parser for the search-criterion grammar (design
    spec §4):

        or_expr     := and_expr ('||' and_expr)*
        and_expr    := not_expr ('&&' not_expr)*
        not_expr    := '!' not_expr | atom
        atom        := '(' or_expr ')' | comparison
        comparison  := IDENT ('contains' | '=' | '<' | '>') STRING
    """

    def __init__(self, text: str) -> None:
        self._tokens = _tokenize(text)
        self._pos = 0

    def parse(self) -> Criterion:
        criterion = self._or_expr()
        if self._pos != len(self._tokens):
            raise ParseError(f"Unexpected trailing input at token {self._pos}")
        return criterion

    def _peek(self) -> tuple[str, str] | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> tuple[str, str]:
        token = self._peek()
        if token is None:
            raise ParseError("Unexpected end of criterion expression")
        self._pos += 1
        return token

    def _or_expr(self) -> Criterion:
        left = self._and_expr()
        while self._peek() and self._peek()[0] == "OR":
            self._advance()
            left = OrCriterion(left, self._and_expr())
        return left

    def _and_expr(self) -> Criterion:
        left = self._not_expr()
        while self._peek() and self._peek()[0] == "AND":
            self._advance()
            left = AndCriterion(left, self._not_expr())
        return left

    def _not_expr(self) -> Criterion:
        if self._peek() and self._peek()[0] == "NOT":
            self._advance()
            return NotCriterion(self._not_expr())
        return self._atom()

    def _atom(self) -> Criterion:
        token = self._peek()
        if token is None:
            raise ParseError("Unexpected end of criterion expression")
        if token[0] == "LPAREN":
            self._advance()
            inner = self._or_expr()
            closing = self._advance()
            if closing[0] != "RPAREN":
                raise ParseError("Expected ')'")
            return inner
        return self._comparison()

    def _comparison(self) -> Criterion:
        field_token = self._advance()
        if field_token[0] != "IDENT":
            raise ParseError(f"Expected a field name, got {field_token[1]!r}")
        field = field_token[1]

        op_token = self._advance()
        if op_token[0] == "IDENT" and op_token[1] == "contains":
            op = "contains"
        elif op_token[0] in ("EQ", "LT", "GT"):
            op = {"EQ": "=", "LT": "<", "GT": ">"}[op_token[0]]
        else:
            raise ParseError(f"Expected an operator, got {op_token[1]!r}")

        value_token = self._advance()
        if value_token[0] != "STRING":
            raise ParseError(f"Expected a quoted value, got {value_token[1]!r}")
        raw_value = _unquote(value_token[1])

        if field in _TIME_FIELDS:
            try:
                value = datetime.fromisoformat(raw_value)
            except ValueError as exc:
                raise ParseError(f"Invalid datetime literal {raw_value!r}") from exc
        else:
            value = raw_value

        return FieldCriterion(field, op, value)


def parse_criterion(text: str) -> Criterion:
    return _CriterionParser(text).parse()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_criteria_parser -v`
Expected: 10 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/criteria_parser.py tests/test_criteria_parser.py
git commit -m "feat: add search-criterion parser (US7 grammar)"
```

---

### Task 7: Persistence (`storage.py`)

**Files:**
- Create: `pim/model/storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Consumes: `PIR`, `PIRRepository.get_all()`, `.next_id`, `.load_snapshot()` (Tasks 2-5), `StorageError` (Task 1).
- Produces: `save(repository: PIRRepository, filename: str) -> str` (returns the actual path written, `.pim`-suffixed), `load(repository: PIRRepository, filename: str) -> str`. Task 8 (`commands.py`, `handle_save`/`handle_load`) calls these exact names.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_storage.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_storage -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.model.storage'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/model/storage.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pim.model.errors import StorageError
from pim.model.pir import PIR
from pim.model.repository import PIRRepository

_EXTENSION = ".pim"


def _normalize_filename(filename: str) -> str:
    if filename.endswith(_EXTENSION):
        return filename
    if "." in Path(filename).name:
        raise StorageError(
            f"'{filename}' has a different extension; .pim files must end in '{_EXTENSION}'"
        )
    return filename + _EXTENSION


def save(repository: PIRRepository, filename: str) -> str:
    path = _normalize_filename(filename)
    payload = {
        "next_id": repository.next_id,
        "pirs": [pir.to_dict() for pir in repository.get_all()],
    }
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    except OSError as exc:
        raise StorageError(f"Could not write '{path}': {exc}") from exc
    return path


def load(repository: PIRRepository, filename: str) -> str:
    path = _normalize_filename(filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise StorageError(f"Could not read '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StorageError(f"'{path}' is not valid JSON: {exc}") from exc

    try:
        next_id = payload["next_id"]
        pirs = [PIR.from_dict(item) for item in payload["pirs"]]
    except (KeyError, TypeError) as exc:
        raise StorageError(f"'{path}' is not a valid .pim file: {exc}") from exc

    repository.load_snapshot(pirs, next_id)
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_storage -v`
Expected: 7 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/model/storage.py tests/test_storage.py
git commit -m "feat: add .pim JSON persistence (US10, US11)"
```

---

### Task 8: Controller (`cli_parser.py`, `commands.py`) and View (`presenter.py`)

**Files:**
- Create: `pim/controller/cli_parser.py`
- Create: `pim/controller/commands.py`
- Create: `pim/view/presenter.py`
- Test: `tests/test_commands.py`

This task's own model-layer dependency (`criteria_parser.parse_criterion`) is already unit-tested (Task 6); this task's tests exercise the wiring, not new model logic, so they're written directly against the finished behavior rather than one micro-TDD cycle per function — still one test method per behavior.

**Interfaces:**
- Consumes: `PIRRepository` (Task 5), `parse_criterion` (Task 6), `save`/`load` (Task 7), `ValidationError`/`PIRNotFoundError`/`ParseError`/`StorageError` (Task 1).
- Produces: `cli_parser.split_command(line) -> (command, remainder)`, `cli_parser.split_args(remainder) -> list[str]`, `commands.run_command(repository, line) -> str` (never raises), `presenter.format_summary/format_detail/format_list/format_error`. Task 9 (`main.py`) calls `split_command` and `run_command`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_commands.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_commands -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pim.controller.commands'`

- [ ] **Step 3: Write minimal implementation**

Create `pim/controller/cli_parser.py`:

```python
from __future__ import annotations

import shlex


def split_command(line: str) -> tuple[str, str]:
    """Split a raw REPL line into (command_name, remainder_text). The
    remainder is left as raw text because commands tokenize it
    differently: `search` hands it whole to the criterion parser, while
    `add`/`edit`/etc. shlex-split it themselves (see split_args)."""
    stripped = line.strip()
    if not stripped:
        return "", ""
    parts = stripped.split(maxsplit=1)
    command = parts[0].lower()
    remainder = parts[1] if len(parts) > 1 else ""
    return command, remainder


def split_args(remainder: str) -> list[str]:
    """Quote-aware split of `remainder` into argument tokens, for commands
    whose arguments are plain values rather than a criterion expression."""
    return shlex.split(remainder)
```

Create `pim/view/presenter.py`:

```python
from __future__ import annotations

from pim.model.pir import PIR

_DETAIL_FIELDS = {
    "Note": ["text"],
    "Task": ["description", "deadline"],
    "Event": ["description", "start_time", "alarm"],
    "Contact": ["name", "address", "mobile_number"],
}


def format_summary(pir: PIR) -> str:
    first_field = _DETAIL_FIELDS[pir.type_name][0]
    preview = getattr(pir, first_field)
    return f"[{pir.id}] {pir.type_name}: {preview}"


def format_detail(pir: PIR) -> str:
    lines = [
        f"id: {pir.id}",
        f"type: {pir.type_name}",
        f"created_at: {pir.created_at.isoformat()}",
        f"modified_at: {pir.modified_at.isoformat()}",
    ]
    for field in _DETAIL_FIELDS[pir.type_name]:
        lines.append(f"{field}: {getattr(pir, field)}")
    return "\n".join(lines)


def format_list(pirs: list[PIR]) -> str:
    if not pirs:
        return "No records found."
    return "\n".join(format_summary(pir) for pir in pirs)


def format_error(exc: Exception) -> str:
    return f"Error: {exc}"
```

Create `pim/controller/commands.py`:

```python
from __future__ import annotations

from datetime import datetime

from pim.controller.cli_parser import split_args, split_command
from pim.model.criteria_parser import parse_criterion
from pim.model.errors import ParseError, PIRNotFoundError, StorageError, ValidationError
from pim.model.repository import PIRRepository
from pim.model.storage import load as storage_load
from pim.model.storage import save as storage_save
from pim.view.presenter import format_detail, format_error, format_list, format_summary

_ADD_FIELDS = {
    "note": ["text"],
    "task": ["description", "deadline"],
    "event": ["description", "start_time", "alarm"],
    "contact": ["name", "address", "mobile_number"],
}
_TIME_FIELDS = {"deadline", "start_time", "alarm"}

HELP_TEXT = """\
Commands:
  add note "<text>"
  add task "<description>" "<deadline ISO datetime>"
  add event "<description>" "<start ISO datetime>" "<alarm ISO datetime>"
  add contact "<name>" "<address>" "<mobile number>"
  edit <id> <field>="<value>" [<field>="<value>" ...]
  print <id>|all
  delete <id>
  search <criterion>   e.g. type="Task" && deadline<"2026-12-01T00:00:00"
  save <filename>
  load <filename>
  help
  exit
"""


def _parse_field_value(field: str, raw: str):
    if field in _TIME_FIELDS:
        try:
            return datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ValidationError(f"'{raw}' is not a valid ISO datetime") from exc
    return raw


def handle_add(repository: PIRRepository, remainder: str) -> str:
    args = split_args(remainder)
    if not args:
        raise ValidationError("Usage: add <note|task|event|contact> <field values...>")
    pir_type_key = args[0].lower()
    values = args[1:]
    if pir_type_key not in _ADD_FIELDS:
        raise ValidationError(
            f"Unknown PIR type '{args[0]}'. Expected one of: {', '.join(_ADD_FIELDS)}"
        )
    field_names = _ADD_FIELDS[pir_type_key]
    if len(values) != len(field_names):
        raise ValidationError(
            f"'add {pir_type_key}' expects {len(field_names)} value(s): {', '.join(field_names)}"
        )
    fields = {name: _parse_field_value(name, raw) for name, raw in zip(field_names, values)}
    pir = repository.add(pir_type_key.capitalize(), **fields)
    return f"Added: {format_summary(pir)}"


def handle_edit(repository: PIRRepository, remainder: str) -> str:
    args = split_args(remainder)
    if len(args) < 2:
        raise ValidationError('Usage: edit <id> <field>="<value>" [<field>="<value>" ...]')
    try:
        pir_id = int(args[0])
    except ValueError:
        raise ValidationError(f"'{args[0]}' is not a valid id") from None

    fields = {}
    for assignment in args[1:]:
        if "=" not in assignment:
            raise ValidationError(f"Expected <field>=<value>, got '{assignment}'")
        field, raw_value = assignment.split("=", 1)
        fields[field] = _parse_field_value(field, raw_value)

    pir = repository.update(pir_id, **fields)
    return f"Updated: {format_summary(pir)}"


def handle_print(repository: PIRRepository, remainder: str) -> str:
    target = remainder.strip()
    if not target:
        raise ValidationError("Usage: print <id>|all")
    if target.lower() == "all":
        return format_list(repository.get_all())
    try:
        pir_id = int(target)
    except ValueError:
        raise ValidationError(f"'{target}' is not a valid id or 'all'") from None
    return format_detail(repository.get(pir_id))


def handle_delete(repository: PIRRepository, remainder: str) -> str:
    target = remainder.strip()
    try:
        pir_id = int(target)
    except ValueError:
        raise ValidationError(f"'{target}' is not a valid id") from None
    repository.delete(pir_id)
    return f"Deleted PIR {pir_id}"


def handle_search(repository: PIRRepository, remainder: str) -> str:
    if not remainder.strip():
        raise ValidationError("Usage: search <criterion expression>")
    criterion = parse_criterion(remainder)
    return format_list(repository.search(criterion))


def handle_save(repository: PIRRepository, remainder: str) -> str:
    filename = remainder.strip()
    if not filename:
        raise ValidationError("Usage: save <filename>")
    path = storage_save(repository, filename)
    return f"Saved to {path}"


def handle_load(repository: PIRRepository, remainder: str) -> str:
    filename = remainder.strip()
    if not filename:
        raise ValidationError("Usage: load <filename>")
    path = storage_load(repository, filename)
    return f"Loaded from {path}"


def handle_help(repository: PIRRepository, remainder: str) -> str:
    return HELP_TEXT


COMMANDS = {
    "add": handle_add,
    "edit": handle_edit,
    "print": handle_print,
    "delete": handle_delete,
    "search": handle_search,
    "save": handle_save,
    "load": handle_load,
    "help": handle_help,
}


def run_command(repository: PIRRepository, line: str) -> str:
    """Top-level entry point used by main.py. Never raises: any PimError
    or bad shlex quoting is caught and turned into a friendly message."""
    command, remainder = split_command(line)
    if not command:
        return ""
    handler = COMMANDS.get(command)
    if handler is None:
        return format_error(ValidationError(f"Unknown command '{command}'. Type 'help' for a list."))
    try:
        return handler(repository, remainder)
    except (ValidationError, PIRNotFoundError, ParseError, StorageError, ValueError) as exc:
        return format_error(exc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_commands -v`
Expected: 14 tests, OK

- [ ] **Step 5: Commit**

```bash
git add pim/controller pim/view tests/test_commands.py
git commit -m "feat: add controller dispatch and view presenter (US1-US11 CLI)"
```

---

### Task 9: `main.py` REPL entry point

**Files:**
- Create: `pim/main.py`

No automated test — this is a thin wiring file (an interactive `input()` loop can't be unit-tested meaningfully without extra indirection this project doesn't need); Task 8's tests already cover `run_command`'s behavior. Verified instead by manual smoke test below.

**Interfaces:**
- Consumes: `split_command` (Task 8's `cli_parser`), `run_command` (Task 8's `commands`), `PIRRepository` (Task 5).
- Produces: `main()` — the process entry point. Nothing downstream depends on this file.

- [ ] **Step 1: Write `pim/main.py`**

```python
from __future__ import annotations

from pim.controller.cli_parser import split_command
from pim.controller.commands import run_command
from pim.model.repository import PIRRepository


def main() -> None:
    repository = PIRRepository()
    print("PIM — Personal Information Manager. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("pim> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        command, _ = split_command(line)
        if command in ("exit", "quit"):
            break
        output = run_command(repository, line)
        if output:
            print(output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manual smoke test**

Run: `python -m pim.main` from the project root, then type:

```
add note "buy milk"
add task "finish report" "2026-12-01T10:00:00"
print all
search text contains "milk"
edit 1 text="buy oat milk"
print 1
save demo
exit
```

Expected: each command prints an `Added:`/`Updated:`/matching-record line with no tracebacks; `print all` lists both records; `search` returns only the note; a `demo.pim` file appears in the project root afterward. Re-run `python -m pim.main`, type `load demo` then `print all` — both records should reappear with the same ids.

- [ ] **Step 3: Commit**

```bash
git add pim/main.py
git commit -m "feat: add REPL entry point"
```

---

### Task 10: Test coverage report

**Files:**
- Create: `htmlcov/` (generated, gitignored — already covered by the `.gitignore` from the earlier commit)
- Create: `coverage_report.txt` (committed — this is the deliverable the assignment asks for)

**Interfaces:**
- Consumes: the full `tests/` suite (Tasks 1-8) and `pim/model/` (Tasks 1-7).
- Produces: `coverage_report.txt` at the project root, per the assignment's requirement to "report the line coverage achieved by your tests on the system model in a separate file... in the root folder of your source code."

- [ ] **Step 1: Install coverage.py (dev-time only — not imported by shipped code)**

```bash
pip install coverage
```

- [ ] **Step 2: Run the full test suite under coverage, scoped to the model package**

```bash
coverage run --source=pim.model -m unittest discover -s tests -v
```

Expected: all tests from Tasks 1-8 pass (the `test_commands.py` tests exercise `pim.model` indirectly too, which is fine — `--source=pim.model` only affects what's *measured*, not what's excluded from running).

- [ ] **Step 3: Generate and save the text report**

```bash
coverage report -m > coverage_report.txt
cat coverage_report.txt
```

Expected: a per-file table (`pim/model/pir.py`, `criteria.py`, `criteria_parser.py`, `repository.py`, `storage.py`, `errors.py`) with a `%` column. If any file is below ~90%, note which lines are uncovered (the `Missing` column) — likely candidates are defensive branches like `StorageError` on an `OSError` during `save`, which the existing tests don't trigger (permission errors are awkward to simulate portably); it's fine to leave a short justification comment in `coverage_report.txt` for any gap rather than writing a brittle test for it.

- [ ] **Step 4: Also generate the HTML view for your own inspection (optional, gitignored)**

```bash
coverage html
open htmlcov/index.html   # macOS
```

- [ ] **Step 5: Commit**

```bash
git add coverage_report.txt
git commit -m "docs: add test coverage report for pim.model"
```

---

## Self-Review Notes

- **Spec coverage:** every spec section maps to a task — §2/§3 architecture and PIR types → Tasks 1-3; §4 criteria + parser → Tasks 4/6; §3 repository → Task 5; §5 persistence → Task 7; §6 error handling → threaded through all tasks via `pim.model.errors`; controller/view/main → Tasks 8-9; §8 testing/coverage → Tasks 1-8 plus Task 10. The two items the spec deliberately left open (CLI command syntax, US8 print-field list) are resolved concretely in Task 8/9 (`_ADD_FIELDS`, `_DETAIL_FIELDS`) rather than left pending, since code can't ship with an open item.
- **Type consistency checked:** `PIRRepository.add(pir_type, **fields)` (Task 5) matches the call in `handle_add` (Task 8); `parse_criterion(text) -> Criterion` (Task 6) matches its use in `handle_search` (Task 8); `save`/`load` signatures (Task 7) match `handle_save`/`handle_load` (Task 8); `split_command`/`split_args` (Task 8) match their use in `main.py` (Task 9) and within `commands.py` itself.
- **No placeholders:** every step has runnable code; nothing deferred to "later."
