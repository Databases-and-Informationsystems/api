import typing

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pdataclass


class SchemaMentionDTO(BaseModel):
    id: typing.Optional[int]
    tag: str


class SchemaRelationDTO(BaseModel):
    id: typing.Optional[int]
    tag: str


class SchemaConstraintDTO(BaseModel):
    id: typing.Optional[int]
    schema_relation: SchemaRelationDTO
    schema_mention_head: SchemaMentionDTO
    schema_mention_tail: SchemaMentionDTO
    is_directed: typing.Optional[bool]


class SchemaDTO(BaseModel):
    _id: typing.Optional[int]
    _schema_mentions: typing.List[SchemaMentionDTO]
    _schema_relations: typing.List[SchemaRelationDTO]
    _schema_constraints: typing.List[SchemaConstraintDTO]
