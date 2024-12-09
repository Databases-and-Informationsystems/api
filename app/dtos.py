from flask_restx import fields
from .extension import api

mention_input_dto = api.model(
    "mention",
    {
        "tag": fields.String,
        "document_edit_id": fields.Integer,
        "token_ids": fields.List(fields.Integer),
        "is_shown_recommendation": fields.Boolean,
        "document_recommendation_id": fields.Integer,
    },
)

mention_output_dto = api.model(
    "mention_output",
    {
        "id": fields.Integer,
        "tag": fields.String,
        "is_shown_recommendation": fields.Boolean,
        "document_edit_id": fields.Integer,
        "document_recommendation_id": fields.Integer,
        "entity_id": fields.Integer,
    },
)
