import abc
import typing
from abc import abstractmethod
from enum import Enum
from typing import final

from app.pipeline.model.document import DocumentEditDTO
from app.pipeline.model.schema import SchemaDTO


class PipelineStepType(Enum):
    TOKENIZER = 1
    MENTION_PREDICTION = 2
    ENTITY_PREDICTION = 3
    RELATION_PREDICTION = 4


class PipelineStep(abc.ABC):
    _pipeline_step_type: PipelineStepType
    _name: str
    _schema: typing.Optional[SchemaDTO]

    def __init__(
        self,
        name: str,
        pipeline_step_type: PipelineStepType,
        schema: typing.Optional[SchemaDTO] = None,
    ):
        self._pipeline_step_type = pipeline_step_type
        self._name = name
        self._schema = schema

    @property
    def name(self):
        return self._name

    @final
    def run(self, document_edit: DocumentEditDTO) -> DocumentEditDTO:
        res = self._run(document_edit)
        return res

    @final
    def train(self):
        self._train()

    @abstractmethod
    def _run(self, document_edit: DocumentEditDTO) -> DocumentEditDTO:
        pass

    @abstractmethod
    def _train(self):
        pass
