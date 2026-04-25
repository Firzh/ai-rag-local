from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext


getcontext().prec = 40


@dataclass(frozen=True)
class CalculatorResult:
    expression: str
    result: str


class CalculatorError(ValueError):
    pass


_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))

    formatted = format(value.normalize(), "f")
    return formatted.rstrip("0").rstrip(".")


def _eval_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise CalculatorError("Boolean tidak didukung.")
        if isinstance(node.value, int | float):
            return Decimal(str(node.value))
        raise CalculatorError("Hanya angka yang didukung.")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError("Operator unary tidak didukung.")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINARY_OPS:
            raise CalculatorError("Operator aritmatika tidak didukung.")

        left = _eval_node(node.left)
        right = _eval_node(node.right)

        if op_type is ast.Pow:
            if right != right.to_integral_value():
                raise CalculatorError("Pangkat desimal tidak didukung.")
            if abs(int(right)) > 12:
                raise CalculatorError("Pangkat terlalu besar.")

        try:
            return Decimal(_BINARY_OPS[op_type](left, right))
        except (DivisionByZero, InvalidOperation, ZeroDivisionError) as exc:
            raise CalculatorError("Operasi matematika tidak valid.") from exc

    raise CalculatorError("Ekspresi mengandung elemen yang tidak didukung.")


def safe_calculate_expression(expression: str) -> CalculatorResult:
    expr = expression.strip()

    if not expr:
        raise CalculatorError("Ekspresi kosong.")

    if len(expr) > 120:
        raise CalculatorError("Ekspresi terlalu panjang.")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("Sintaks ekspresi tidak valid.") from exc

    value = _eval_node(tree)
    return CalculatorResult(expression=expr, result=_format_decimal(value))