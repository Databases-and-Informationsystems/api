from flask_restx import Namespace, Resource
from app.services.entity_service import entity_service
from werkzeug.exceptions import BadRequest
from app.dtos import entity_output_list_dto

ns = Namespace("entities", description="Entity related operations")


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class EntityQueryResource(Resource):
    service = entity_service

    @ns.doc(description="Get Entities of document annotation")
    @ns.marshal_with(entity_output_list_dto)
    def get(self, document_edit_id):
        if not document_edit_id:
            raise BadRequest("Document Edit ID is required.")

        response = self.service.get_entities_by_document_edit(document_edit_id)
        return response
