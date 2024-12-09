from flask import request, jsonify
from . import mentions
from werkzeug.exceptions import HTTPException, BadRequest
from flask_restx import Resource, Namespace
from app.dtos import mention_input_dto
from app.dtos import mention_output_dto
from app.services.mention_services import mention_service

ns = Namespace("api", description="Mention Relations API")


@mentions.route("/<document_edit_id>", methods=["GET"])
def get_mentions_by_document_edit(document_edit_id):
    try:
        if not document_edit_id:
            raise BadRequest("Document Edit ID is required.")

        if not document_edit_id.isdigit():
            raise BadRequest("Document Edit ID must be a valid integer.")

        document_edit_id = int(document_edit_id)

        response, status = mention_service.get_mentions_by_document_edit(
            document_edit_id
        )
        return jsonify(response), status

    except HTTPException as e:
        return jsonify({"message": str(e)}), e.code

    except Exception as e:
        return (
            jsonify({"message": "An unexpected error occurred.", "details": str(e)}),
            500,
        )


@ns.route("/mentions")
class MentionResource(Resource):

    @ns.expect(mention_input_dto)
    @ns.marshal_with(mention_output_dto)
    def post(self):
        return mention_service.create_mentions(mention_input_dto)
