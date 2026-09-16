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

    def update(self, pir_id: int, **fields) -> PIR:
        pir = self.get(pir_id)
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
