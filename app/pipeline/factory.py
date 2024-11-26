import typing

from app.pipeline import Pipeline
from app.pipeline.model.document import DocumentEditDTO
from app.pipeline.steps.tokenizer import Tokenizer


class PipelineFactory:

    @staticmethod
    def create(
        document_edit: DocumentEditDTO, settings: typing.Optional[any] = None
    ) -> Pipeline:
        pipeline_steps = [Tokenizer()]

        return Pipeline(pipeline_steps, document_edit)
