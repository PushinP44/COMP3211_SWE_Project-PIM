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
