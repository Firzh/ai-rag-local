from __future__ import annotations

import re

from app.tools.calculator import CalculatorError, CalculatorResult, safe_calculate_expression


_MATH_INTENT_WORDS = (
    "berapa",
    "hitung",
    "hasil",
    "kalkulasi",
    "calculate",
    "calculator",
    "kalkulator",
    "pangkat",
)


def _looks_like_arithmetic_query(query: str) -> bool:
    lower = query.lower()
    has_digit = bool(re.search(r"\d", lower))

    if not has_digit:
        return False

    has_strong_operator = bool(
        re.search(r"\d\s*(\*|/|×|÷|\^)\s*\d", lower)
        or re.search(r"\d\s*\*\*\s*\d", lower)
    )
    has_math_intent = any(word in lower for word in _MATH_INTENT_WORDS)
    has_equal_arithmetic = bool(
        re.search(r"\d\s*[+\-*/^]\s*\d\s*=", lower)
        or re.search(r"\d\s*\*\*\s*\d\s*=", lower)
    )

    return has_strong_operator or has_math_intent or has_equal_arithmetic

def _normalize_expression(query: str) -> str:
    expr = query.lower()

    expr = expr.replace("×", "*")
    expr = expr.replace("÷", "/")
    expr = expr.replace("^", "**")

    # Ubah 17 x 23 menjadi 17 * 23, tetapi jangan ubah huruf x bebas.
    expr = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", expr)

    # Ubah koma desimal Indonesia menjadi titik desimal.
    expr = re.sub(r"(?<=\d),(?=\d)", ".", expr)

    # Buang kata umum, tanda tanya, dan bagian setelah sama dengan.
    expr = expr.replace("?", " ")
    expr = expr.split("=")[0]

    # Sisakan hanya karakter aritmatika aman.
    expr = re.sub(r"[^0-9+\-*/().\s]", " ", expr)
    expr = re.sub(r"\s+", "", expr)

    # Hindari operator menggantung.
    expr = expr.strip("+-*/.")

    return expr


def try_calculate_query(query: str) -> CalculatorResult | None:
    if not _looks_like_arithmetic_query(query):
        return None

    expression = _normalize_expression(query)

    if not expression:
        return None

    if not re.search(r"\d", expression):
        return None

    if not re.search(r"[+\-*/]", expression):
        return None

    try:
        return safe_calculate_expression(expression)
    except CalculatorError:
        return None