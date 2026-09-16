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
