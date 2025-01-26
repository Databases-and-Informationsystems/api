from app.services.relation_services import relation_service
from werkzeug.exceptions import BadRequest
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.dtos import (
    relation_output_list_dto,
    relation_output_dto,
    relation_input_dto,
    relation_update_input_dto,
)
from flask import request

ns = Namespace("relations", description="Relation related operations")


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationQueryResource(Resource):
    service = relation_service

    @jwt_required()
    @ns.doc(description="Get Relations of document annotation")
    @ns.marshal_with(relation_output_list_dto)
    def get(self, document_edit_id):
        if not document_edit_id:
            raise BadRequest("Document Edit ID is required.")

        response = self.service.get_relations_by_document_edit(document_edit_id)
        return response


@ns.route("/<int:relation_id>")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationDeleteResource(Resource):
    service = relation_service

    @ns.doc(description="Delete a Relation by ID")
    @jwt_required()
    def delete(self, relation_id):
        response = self.service.delete_relation_by_id(relation_id)
        return response, 200

    @ns.expect(relation_update_input_dto)
    @ns.marshal_with(relation_output_dto)
    @ns.doc(description="Update a Relation by ID")
    @jwt_required()
    def patch(self, relation_id):
        data = request.get_json()
        schema_relation_id = data.get("schema_relation_id")
        mention_head_id = data.get("mention_head_id")
        mention_tail_id = data.get("mention_tail_id")
        is_directed = data.get("isDirected")
        response = self.service.update_relation(
            relation_id,
            schema_relation_id,
            mention_head_id,
            mention_tail_id,
            is_directed,
        )
        return response


@ns.route("")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationCreationResource(Resource):
    service = relation_service

    @ns.doc(description="Create a new relation")
    @ns.marshal_with(relation_output_dto)
    @ns.expect(relation_input_dto)
    @jwt_required()
    def post(self):
        response = self.service.create_relation(request.json)
        return response


@ns.route("/<int:relation_id>/accept")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(400, "Invalid input")
@ns.response(404, "Relation not found")
class RelationAcceptResource(Resource):

    @ns.marshal_with(relation_output_dto)
    @ns.doc(description="Accept a relation by copying it and marking it as processed")
    @jwt_required()
    def post(self, relation_id):
        """
        Accept a relation by copying it to the document edit and setting isShownRecommendation to False.
        """

        return relation_service.accept_relation(relation_id)


@ns.route("/<int:relation_id>/reject")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(400, "Invalid input")
@ns.response(404, "Relation not found")
class RelationRejectResource(Resource):

    @ns.doc(description="Reject a relation by marking it as processed")
    @jwt_required()
    def post(self, relation_id):
        """
        Reject a relation by setting isShownRecommendation to False.
        """

        return relation_service.reject_relation(relation_id)
