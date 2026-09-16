from __future__ import annotations

import json
from pathlib import Path

from pim.model.errors import StorageError, ValidationError
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
        if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 1:
            raise TypeError(f"'next_id' must be a positive integer, got {next_id!r}")
        pirs = [PIR.from_dict(item) for item in payload["pirs"]]
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise StorageError(f"'{path}' is not a valid .pim file: {exc}") from exc

    repository.load_snapshot(pirs, next_id)
    return path
