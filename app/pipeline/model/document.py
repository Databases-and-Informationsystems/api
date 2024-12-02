import typing
from enum import Enum

from pydantic import BaseModel

from app.models import Document


class TokenDTO(BaseModel):
    id: typing.Optional[int]
    text: str
    document_index: int
    sentence_index: int
    pos_tag: str


class EntityDTO(BaseModel):
    id: int


class MentionDTO(BaseModel):
    tag: str
    tokens: typing.List[TokenDTO]
    entity: typing.Optional[EntityDTO]


class RelationDTO(BaseModel):
    id: int
    tag: str
    head_mention: MentionDTO
    tail_mention: MentionDTO


class DocumentStateDTO(Enum):
    NEW = 1
    IN_PROGRESS = 2
    FINISHED = 3


class DocumentDTO(BaseModel):
    id: int
    name: str
    content: str
    state: typing.Optional[DocumentStateDTO]
    tokens: typing.Optional[typing.List[TokenDTO]]

    @staticmethod
    def from_document(document: Document) -> "DocumentDTO":
        return DocumentDTO(
            id=int(document.id),
            name=str(document.name),
            content=str(document.content),
            state=DocumentStateDTO(int(document.state_id)),
            tokens=None,
        )


class DocumentEditStateDTO(Enum):
    MENTIONS = 1
    ENTITIES = 2
    RELATIONS = 3
    FINISHED = 4

    def to_dict(self):
        if self.MENTIONS:
            return "MENTIONS"
        elif self.ENTITIES:
            return "ENTITIES"
        elif self.RELATIONS:
            return "RELATIONS"
        elif self.FINISHED:
            return "FINISHED"


class DocumentEditDTO(BaseModel):
    document: DocumentDTO
    state: typing.Optional[DocumentEditStateDTO]
    mentions: typing.Optional[typing.List[MentionDTO]]
    relations: typing.Optional[typing.List[RelationDTO]]
    entities: typing.Optional[typing.List[EntityDTO]]
