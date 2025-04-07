from sqlmodel import SQLModel, Field
from sqlmodel.sql.sqltypes import AutoString
from typing import Optional
from enum import Enum
import json


class ConceptType(str, Enum):
    ACTIVITY = "ACTIVITY"
    METRIC = "METRIC"
    STATE = "STATE"
    LOCATION = "LOCATION"


class SourceType(str, Enum):
    MANUAL = "MANUAL"
    SENSOR = "SENSOR"
    APPLICATION = "APPLICATION"
    API = "API"
    PLUGIN = "PLUGIN"


class Concept(SQLModel, table=True):
    concept_id: str = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    parent_concept_id: Optional[str] = Field(
        default=None, foreign_key="concept.concept_id"
    )
    type: Optional[ConceptType] = None
    meta_json: str = Field(default="{}", sa_type=AutoString)

    @property
    def meta(self) -> dict:
        return json.loads(self.meta_json)

    @meta.setter
    def meta(self, value: dict):
        self.meta_json = json.dumps(value)


class Source(SQLModel, table=True):
    source_id: str = Field(primary_key=True)
    name: str
    type: SourceType
    description: Optional[str] = None
    meta_json: str = Field(default="{}", sa_type=AutoString)

    @property
    def meta(self) -> dict:
        return json.loads(self.meta_json)

    @meta.setter
    def meta(self, value: dict):
        self.meta_json = json.dumps(value)


class Stream(SQLModel, table=True):
    stream_id: str = Field(primary_key=True)
    concept_id: str = Field(foreign_key="concept.concept_id")
    source_id: str = Field(foreign_key="source.source_id")
    name: Optional[str] = None
    description: Optional[str] = None
    meta_json: str = Field(default="{}", sa_type=AutoString)

    @property
    def meta(self) -> dict:
        return json.loads(self.meta_json)

    @meta.setter
    def meta(self, value: dict):
        self.meta_json = json.dumps(value)
