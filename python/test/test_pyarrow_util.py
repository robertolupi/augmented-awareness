import pytest
import pyarrow as pa
import pydantic
import datetime
import uuid
from typing import Optional, List, Dict
from aww.pyarrow_util import pydantic_to_pyarrow_schema, pydantic_to_pyarrow_table


# Test models
class SimpleModel(pydantic.BaseModel):
    name: str
    age: int
    is_active: bool


class OptionalModel(pydantic.BaseModel):
    required: str
    optional: Optional[str]


class NestedModel(pydantic.BaseModel):
    simple: SimpleModel
    timestamp: datetime.datetime


class ComplexTypesModel(pydantic.BaseModel):
    uuid: uuid.UUID
    numbers: List[int]
    metadata: Dict[str, str]


# Test cases
def test_pydantic_to_pyarrow_schema_simple():
    schema = pydantic_to_pyarrow_schema(SimpleModel)
    assert isinstance(schema, pa.Schema)
    assert schema.names == ["name", "age", "is_active"]
    assert schema.types == [pa.string(), pa.int64(), pa.bool_()]


def test_pydantic_to_pyarrow_schema_optional():
    schema = pydantic_to_pyarrow_schema(OptionalModel)
    assert schema.field("required").type == pa.string()
    assert schema.field("required").nullable is False
    assert schema.field("optional").type == pa.string()
    assert schema.field("optional").nullable is True


def test_pydantic_to_pyarrow_schema_nested():
    schema = pydantic_to_pyarrow_schema(NestedModel)
    assert isinstance(schema.field("simple").type, pa.StructType)
    assert schema.field("timestamp").type == pa.timestamp("us")


def test_pydantic_to_pyarrow_schema_complex():
    schema = pydantic_to_pyarrow_schema(ComplexTypesModel)
    assert schema.field("uuid").type == pa.string()
    assert isinstance(schema.field("numbers").type, pa.ListType)
    assert schema.field("numbers").type.value_type == pa.int64()
    assert isinstance(schema.field("metadata").type, pa.MapType)


def test_pydantic_to_pyarrow_table_simple():
    data = [
        SimpleModel(name="Alice", age=30, is_active=True),
        SimpleModel(name="Bob", age=25, is_active=False),
    ]
    table = pydantic_to_pyarrow_table(data, SimpleModel)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table.schema.names == ["name", "age", "is_active"]


def test_pydantic_to_pyarrow_table_nested():
    now = datetime.datetime.now()
    with pytest.raises(pa.lib.ArrowTypeError):
        data = [
            NestedModel(
                simple=SimpleModel(name="Test", age=10, is_active=True), timestamp=now
            )
        ]
        pydantic_to_pyarrow_table(data, NestedModel)


def test_pydantic_to_pyarrow_table_wrong_type():
    with pytest.raises(TypeError):
        pydantic_to_pyarrow_table(["not a model"], SimpleModel)


def test_pydantic_to_pyarrow_table_wrong_class():
    with pytest.raises(TypeError):
        pydantic_to_pyarrow_table(
            [SimpleModel(name="x", age=1, is_active=True)], OptionalModel
        )
