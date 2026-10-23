"""JSON serialization for eval inputs and results."""

import json
import math
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


def validate_rows(rows):
    """Require a rectangular JSON table with scalar cells."""
    if not isinstance(rows, list) or any(not isinstance(row, list) for row in rows):
        raise ValueError("Return rows as an array of arrays, including for a single value.")
    if rows and (not rows[0] or any(len(row) != len(rows[0]) for row in rows)):
        raise ValueError("Each row must have the same nonzero number of columns.")
    for row in rows:
        for value in row:
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise ValueError("Answer cells must be strings, numbers, booleans, or null.")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Answer numbers must be finite.")


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Unsupported result type: {type(value).__name__}")


def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=json_value)


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=json_value) + "\n")
