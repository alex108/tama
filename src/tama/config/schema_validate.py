from datetime import datetime
from dataclasses import is_dataclass
from typing import (
    Type, TypeVar, Any, Union, get_type_hints, get_origin, get_args
)

__all__ = ["validate_map_schema"]

T = TypeVar("T")

PRIMITIVE_TYPES = (str, int, float, bool, datetime, list, dict)


def is_optional(field) -> bool:
    return get_origin(field) is Union and type(None) in get_args(field)


def get_optional_args(field):
    args = tuple(t for t in get_args(field) if t is not type(None))
    if len(args) == 1:
        return args[0]
    else:
        return Union[args]


def validate_map_schema(obj: Any, schema: Type[T], key: str = "") -> T:
    """
    Validates that configuration schema corresponds to the given schema
    and maps it to an object of the given schema type.

    :param obj: Validated object.
    :param schema: Schema type.
    :param key: Indicates current key being validated for error reporting.
    :return:
    """
    # Ignore optionals set to None, else do the usual check
    if is_optional(schema):
        if obj is None:
            return None
        schema = get_optional_args(schema)
    else:
        if obj is None:
            raise ValueError(
                f"Expected key {key} to be set. Found no value."
            )

    # If schema is a primitive type just validate said primitive
    if schema in PRIMITIVE_TYPES:
        if not isinstance(obj, schema):
            raise TypeError(
                f"Bad type at {key}: Expected {schema.__name__}, got "
                f"{type(key).__name__}."
            )
        else:
            return obj

    # If schema is a dataclass, check each field
    if is_dataclass(schema):
        # Dataclass representation must be Dict[str, Any]
        if not isinstance(obj, dict):
            raise TypeError(
                f"Bad type at {key}: Expected dict, got "
                f"{type(obj).__name__}."
            )

        # __init__ params
        kwargs = {}
        for k, v in get_type_hints(schema).items():
            if key == "":
                full_key = k
            else:
                full_key = key + "." + k
            m = validate_map_schema(obj.get(k), v, key=full_key)
            kwargs[k] = m

        return schema(**kwargs)

    # Else this should be a type hint
    origin = get_origin(schema)
    args = get_args(schema)
    if origin is dict:
        if not isinstance(obj, dict):
            raise TypeError(
                f"Bad type at {key}: Expected dict, got "
                f"{type(obj).__name__}."
            )

        mapped_dict = {}
        for k, v in obj.items():
            # Don't bother validating keys because they will always be
            # str in TOML.
            m = validate_map_schema(v, args[1], key=key + "." + k)
            mapped_dict[k] = m
        return mapped_dict
    elif origin is list:
        if not isinstance(obj, list):
            raise TypeError(
                f"Bad type at {key}: Expected list, got "
                f"{type(obj).__name__}."
            )

        mapped_list = []
        for i, elem in enumerate(obj):
            m = validate_map_schema(elem, args[1], key=key + "." + str(i))
            mapped_list.append(m)
        return mapped_list

    raise TypeError("Unsupported schema type: " + repr(schema))
