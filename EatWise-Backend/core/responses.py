"""Unified success envelope helpers."""
from typing import Any


def ok(data: Any = None) -> dict:
    return {"success": True, "data": data}
