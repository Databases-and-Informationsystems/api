from flask_restx import Namespace, Resource

from app.db import transactional
from app.models import DocumentEdit
from app.services.document_edit_service import document_edit_service

from app.services.user_service import user_service
from flask import request
from app.dtos import (
    document_edit_output_dto,
    document_edit_input_dto,
    document_edit_output_soft_delete_dto,
    document_edit_get_output_dto,
)
from flask_jwt_extended import jwt_required

ns = Namespace("annotations", description="Document-Annotation related operations")


@ns.route("/")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentRoutes(Resource):
    service = document_edit_service

    @jwt_required()
    @ns.doc(description="Create a new document annotation")
    @ns.marshal_with(document_edit_output_dto)
    @ns.expect(document_edit_input_dto, validate=True)
    @transactional
    def post(self):
        request_data = request.get_json()

        response = self.service.create_document_edit(request_data["document_id"])
        return response


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditDeletionResource(Resource):
    service = document_edit_service
    user_service = user_service

    @jwt_required()
    @ns.marshal_with(document_edit_get_output_dto)
    def get(self, document_edit_id):
        user_service.check_user_document_edit_accessible(
            user_service.get_logged_in_user_id(), document_edit_id
        )

        document_edit: DocumentEdit = self.service.get_by_id(document_edit_id)

        return document_edit.to_dict()

    @jwt_required()
    @ns.marshal_with(document_edit_output_soft_delete_dto)
    @ns.doc(description="Soft-delete a DocumentEdit by setting 'active' to False")
    def delete(self, document_edit_id):
        response = self.service.soft_delete_document_edit(document_edit_id)
        return response
