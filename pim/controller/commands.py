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
    args = split_args(remainder)
    if len(args) != 1:
        raise ValidationError("Usage: save <filename>")
    path = storage_save(repository, args[0])
    return f"Saved to {path}"


def handle_load(repository: PIRRepository, remainder: str) -> str:
    args = split_args(remainder)
    if len(args) != 1:
        raise ValidationError("Usage: load <filename>")
    path = storage_load(repository, args[0])
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
