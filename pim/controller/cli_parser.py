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
