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
