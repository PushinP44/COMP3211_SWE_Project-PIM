# PIM — Personal Information Manager (COMP3211 Course Project)

A command-line Personal Information Management system built for **COMP3211
Software Engineering** (Fall 2026). Supports creating, editing, searching,
printing, and deleting personal information records (notes, tasks, events,
contacts), plus saving/loading them to `.pim` files — covering all 11 user
stories in the [project brief](Project%20Description%20-%202026.pdf).

## Requirements

- Python 3.11+ (developed and tested on 3.12.4)
- No third-party runtime dependencies — standard library only
- `coverage` (optional, dev-only) to regenerate `coverage_report.txt`

## Running the system

```bash
python -m pim.main
```

This starts an interactive REPL. Type `help` for the full command
reference, or see below for a quick example:

```
pim> add note "buy milk"
Added: [1] Note: buy milk
pim> add task "finish report" "2026-12-01T10:00:00"
Added: [2] Task: finish report
pim> search text contains "milk"
[1] Note: buy milk
pim> edit 1 text="buy oat milk"
Updated: [1] Note: buy oat milk
pim> save backup
Saved to backup.pim
pim> exit
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

98 tests, all targeting the `pim.model` package (the assignment only
requires — and grades — unit tests scoped to the model).

To regenerate the coverage report:

```bash
pip install coverage
coverage run --source=pim.model -m unittest discover -s tests -v
coverage report -m > coverage_report.txt
```

## Project structure

```
pim/
  model/        # domain logic — the only package the assignment requires unit tests for
    pir.py            # PIR base class + Note/Task/Event/Contact + registry
    criteria.py        # search-criterion classes (Composite pattern, US7)
    criteria_parser.py # tokenizer + recursive-descent parser for search expressions
    repository.py      # in-memory CRUD + search (US1, US6, US7, US9)
    storage.py          # .pim JSON persistence (US10, US11)
    errors.py           # shared exception hierarchy
  controller/
    cli_parser.py      # splits a raw REPL line into command + arguments
    commands.py         # command dispatch table and handlers
  view/
    presenter.py       # formats PIRs and messages for console output
  main.py               # REPL entry point

tests/                  # unit tests (unittest), one file per pim.model module,
                         # plus tests/test_commands.py for the CLI dispatch layer

docs/superpowers/
  specs/                # design spec (architecture, data model, search grammar, persistence)
  plans/                # the TDD implementation plan the code was built from
```

## Documentation

- [Design spec](docs/superpowers/specs/2026-09-15-pim-cli-system-design.md) —
  architecture, domain model, search-criterion grammar, persistence format,
  and the project timeline.
- [Implementation plan](docs/superpowers/plans/2026-09-16-pim-cli-implementation.md) —
  the task-by-task TDD plan the code was built from.
- [Test coverage report](coverage_report.txt)
