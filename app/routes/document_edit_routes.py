from flask_restx import Namespace, Resource
from app.services.document_edit_service import document_edit_service
from flask import request

from app.dtos import document_edit_output_dto, document_edit_input_dto

ns = Namespace("annotations", description="Document-Annotation related operations")


@ns.route("/")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentRoutes(Resource):
    service = document_edit_service

    @ns.doc(description="Create a new document annotation")
    @ns.marshal_with(document_edit_output_dto)
    @ns.expect(document_edit_input_dto, validate=True)
    def post(self):
        request_data = request.get_json()

        response = self.service.create_document_edit(request_data["document_id"])
        return response
