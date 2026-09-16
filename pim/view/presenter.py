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
