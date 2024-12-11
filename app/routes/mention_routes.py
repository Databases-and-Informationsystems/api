from flask import request
from werkzeug.exceptions import BadRequest
from flask_restx import Resource, Namespace
from app.services.mention_services import mention_service
from app.dtos import mention_output_dto, mention_output_list_dto, mention_input_dto

ns = Namespace("mentions", description="Mention related operations")


@ns.route("/")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class MentionResource(Resource):
    service = mention_service

    @ns.expect(mention_input_dto)
    @ns.marshal_with(mention_output_dto)
    def post(self):
        return self.service.create_mentions(request.json)


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class MentionQueryResource(Resource):
    service = mention_service

    @ns.doc(description="Get Mentions of document annotation")
    @ns.marshal_with(mention_output_list_dto)
    def get(self, document_edit_id):
        if not document_edit_id:
            raise BadRequest("Document Edit ID is required.")

        response = self.service.get_mentions_by_document_edit(document_edit_id)
        return response
