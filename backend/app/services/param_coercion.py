import inspect
import json
from typing import Any, Optional, get_origin

from pydantic import TypeAdapter
from pydantic_core import ValidationError


_TRUE_STRINGS = {"true", "1", "yes", "y", "on"}
_FALSE_STRINGS = {"false", "0", "no", "n", "off"}


def _normalize_empty_string(value: Any) -> Any:
    if isinstance(value, str) and value == "":
        return None
    return value


def _fallback_coerce_by_default(value: Any, default_value: Any) -> Any:
    """
    Best-effort coercion when we don't have type annotations.
    Uses default_value's runtime type as the target.
    """
    if value is None or default_value is None:
        return value

    default_type = type(default_value)
    if isinstance(value, default_type):
        return value

    try:
        if default_type is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in _TRUE_STRINGS:
                    return True
                if lowered in _FALSE_STRINGS:
                    return False
            # Unknown bool-ish string: keep original to avoid surprising flips
            return value

        if default_type in (list, dict) and isinstance(value, str):
            # Try to parse JSON strings into containers.
            parsed = json.loads(value)
            if default_type is list and isinstance(parsed, list):
                return parsed
            if default_type is dict and isinstance(parsed, dict):
                return parsed
            return value

        # For numeric / str-like types
        return default_type(value)
    except Exception:
        return value


def coerce_param_value(
    value: Any,
    *,
    annotation: Any = inspect.Parameter.empty,
    default_value: Any = None,
) -> Any:
    """
    Coerce a single parameter value to the expected type.

    Priority:
    1) Use Pydantic TypeAdapter when annotation exists.
       - validate_python for normal values
       - validate_json when value is a JSON string (useful for list/dict/typed containers)
    2) Fall back to coercion based on default_value runtime type.
    """
    value = _normalize_empty_string(value)

    if value is not None and annotation is not inspect.Parameter.empty:
        try:
            adapter = TypeAdapter(annotation)
            try:
                return adapter.validate_python(value)
            except ValidationError:
                # If frontend sent JSON-as-string, attempt JSON validation for typed containers.
                if isinstance(value, str):
                    return adapter.validate_json(value)
        except Exception:
            # Any adapter/validation errors: fall back below.
            pass

    value = _fallback_coerce_by_default(value, default_value)

    # If we still have a string that looks like JSON and default_value is an empty container
    # without reliable typing, try a last resort parse for list/dict.
    if isinstance(value, str) and default_value is not None:
        origin = get_origin(annotation)
        if origin in (list, dict) or isinstance(default_value, (list, dict)):
            try:
                parsed = json.loads(value)
                return parsed
            except Exception:
                return value

    return value

