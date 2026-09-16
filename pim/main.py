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
