from . import main
from flask import jsonify

from ..models import Document
from ..pipeline.factory import PipelineFactory
from ..pipeline.model.document import DocumentEditDTO, DocumentDTO


@main.route("/api/data", methods=["GET"])
def get_data():
    return jsonify({"message": "Nlp project backend"})


@main.route("/api/test", methods=["GET"])
def test_pipeline():
    # TODO this should be on service level with a better way of getting the document
    document = Document.query.get({"id": 1})
    d = DocumentDTO.from_document(document)
    document_edit: DocumentEditDTO = DocumentEditDTO(
        document=d, state=None, mentions=None, relations=None, entities=None
    )
    pipeline = PipelineFactory.create(document_edit)

    for pipeline_step in pipeline.get_pipeline_steps():
        document_edit = pipeline_step.run(document_edit)
    return document_edit.json()
