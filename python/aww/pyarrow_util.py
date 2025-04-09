import pyarrow as pa
import pydantic
import datetime
import decimal
import uuid
import enum
from typing import Type, get_origin, get_args, Union, List, Dict, Any, Literal

# Mapping from Python types to PyArrow types
# We handle complex types like List, Optional, Union, BaseModel recursively
_PYDANTIC_TO_PYARROW_TYPE_MAP = {
    int: pa.int64(),
    float: pa.float64(),
    str: pa.string(),
    bool: pa.bool_(),
    bytes: pa.binary(),
    datetime.datetime: pa.timestamp('us'),
    datetime.date: pa.date32(),
    datetime.time: pa.time64('us'),
    decimal.Decimal: pa.string(), # Safest default for Decimal without precision/scale
    uuid.UUID: pa.string(),
}

def _is_optional(field_annotation: Type) -> bool:
    """Checks if a type annotation is Optional[T] or Union[T, None]."""
    origin = get_origin(field_annotation)
    if origin is Union:
        args = get_args(field_annotation)
        return type(None) in args
    # Python 3.10+ uses | syntax for Union
    if hasattr(field_annotation, '__args__') and type(None) in field_annotation.__args__:
        # Check specifically for T | None type structure
        if len(field_annotation.__args__) == 2 and isinstance(None, field_annotation.__args__[1]):
            return True
    return False

def _get_non_optional_type(field_annotation: Type) -> Type:
    """Extracts T from Optional[T] or Union[T, None]."""
    if not _is_optional(field_annotation):
        return field_annotation

    origin = get_origin(field_annotation)
    if origin is Union:
        args = get_args(field_annotation)
        # Return the first non-None type
        return next(arg for arg in args if arg is not type(None))
    # Python 3.10+ | syntax
    if hasattr(field_annotation, '__args__') and type(None) in field_annotation.__args__:
        # Return the first non-None type
        return next(arg for arg in field_annotation.__args__ if arg is not type(None))

    # Should not happen if _is_optional is true, but as a fallback
    return field_annotation


def get_pyarrow_type(field_annotation: Type) -> pa.DataType:
    """Recursively determines the PyArrow type for a given Python type annotation."""

    # Handle Optional[T] or T | None
    core_type = _get_non_optional_type(field_annotation)
    origin = get_origin(core_type)
    args = get_args(core_type)

    # Basic types
    if core_type in _PYDANTIC_TO_PYARROW_TYPE_MAP:
        return _PYDANTIC_TO_PYARROW_TYPE_MAP[core_type]

    # Enums -> String representation
    if isinstance(core_type, type) and issubclass(core_type, enum.Enum):
        return pa.string()

    # Literals -> Treat as underlying type (usually string or int)
    if origin is Literal:
        # Check the type of the first literal value
        if args:
            literal_val_type = type(args[0])
            # Recursively find the pyarrow type for the literal's base type
            return get_pyarrow_type(literal_val_type)
        else:
            # Empty literal? Fallback to string or raise error
            return pa.string()


    # List[T]
    if origin is list or origin is List:
        if not args:
            raise TypeError("List type hint must specify element type, e.g., List[int]")
        element_type = get_pyarrow_type(args[0])
        return pa.list_(element_type)

    # Dict[K, V] -> MapType (often restricted to Dict[str, V])
    if origin is dict or origin is Dict:
        if not args or len(args) != 2:
            raise TypeError("Dict type hint must specify key and value types, e.g., Dict[str, int]")
        key_type = args[0]
        value_type = args[1]

        # Arrow Maps typically require string keys
        if key_type is not str:
            # Option 1: Raise error
            # raise TypeError(f"PyArrow map keys usually must be strings, got {key_type}")
            # Option 2: Convert dict to JSON string (less structured)
            print(f"Warning: Dictionary key type {key_type} is not string. Representing field as JSON string.")
            return pa.string()


        pa_value_type = get_pyarrow_type(value_type)
        return pa.map_(pa.string(), pa_value_type)


    # Nested Pydantic BaseModel -> Struct
    if isinstance(core_type, type) and issubclass(core_type, pydantic.BaseModel):
        # Recursively generate schema for nested model
        nested_schema = pydantic_to_pyarrow_schema(core_type)
        return pa.struct(nested_schema)

    # Union[T1, T2, ...] (excluding Optional) - Complex Case
    if origin is Union:
        # Arrow's Union type is complex to map directly.
        # Common strategy: Use a dense union if types are known and limited,
        # or default to a less specific type like string or binary.
        # For simplicity, we'll raise an error here.
        raise TypeError(f"Complex Union types (excluding Optional) like {core_type} are not directly supported yet.")

    # Catch-all for unsupported types
    if core_type is Any:
        print("Warning: 'Any' type encountered. Mapping to pa.null() - data loss may occur.")
        return pa.null()

    raise TypeError(f"Unsupported type for PyArrow conversion: {core_type} (original: {field_annotation})")


def pydantic_to_pyarrow_schema(model_class: Type[pydantic.BaseModel]) -> pa.Schema:
    """
    Builds a pyarrow.Schema from a Pydantic BaseModel class.

    Args:
        model_class: The Pydantic BaseModel class (not an instance).

    Returns:
        A pyarrow.Schema corresponding to the Pydantic model.

    Raises:
        TypeError: If an unsupported Pydantic field type is encountered.
    """
    if not isinstance(model_class, type) or not issubclass(model_class, pydantic.BaseModel):
        raise TypeError("Input must be a Pydantic BaseModel class.")

    arrow_fields = []
    # Use model_fields for Pydantic V2+
    if hasattr(model_class, 'model_fields'):
        fields_dict = model_class.model_fields
    else:
        # Fallback for Pydantic V1 (less common now)
        fields_dict = getattr(model_class, '__fields__', {})
        if not fields_dict:
            raise AttributeError("Could not find fields information on the model. Ensure it's a valid Pydantic model.")


    for field_name, field_info in fields_dict.items():
        # In Pydantic V2, the annotation is directly on field_info
        # In Pydantic V1, it might be field_info.outer_type_
        field_annotation = getattr(field_info, 'annotation', None)
        if field_annotation is None and hasattr(field_info, 'outer_type_'): # Pydantic V1 check
            field_annotation = field_info.outer_type_
        elif field_annotation is None:
            raise TypeError(f"Could not determine annotation for field '{field_name}'")


        try:
            arrow_type = get_pyarrow_type(field_annotation)
            is_nullable = _is_optional(field_annotation)
            arrow_fields.append(pa.field(field_name, arrow_type, nullable=is_nullable))
        except TypeError as e:
            raise TypeError(f"Error processing field '{field_name}': {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error processing field '{field_name}' with annotation {field_annotation}: {e}") from e


    return pa.schema(arrow_fields)
