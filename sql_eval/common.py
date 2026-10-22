"""Stable serialization and artifact identities."""

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Unsupported result type: {type(value).__name__}")


def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=json_value)


def digest(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=json_value) + "\n")
