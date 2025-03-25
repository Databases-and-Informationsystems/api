import typing

from app.models.buisness_models import BRelation
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.relation_services import relation_service, RelationService
from flask_restx import Namespace
from app.dtos import (
    relation_output_model,
    relation_input_dto,
    relation_update_input_dto,
)
from flask import request

ns = Namespace("relations", description="Relation related operations")


class RelationBaseRoute(AuthorizedBaseRoute):
    service: RelationService = relation_service


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationQueryResource(RelationBaseRoute):

    @ns.marshal_with(relation_output_model, as_list=True)
    def get(self, document_edit_id):
        """
        Fetch all relations of document annotation.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        relations: typing.List[BRelation] = self.service.get_relations_by_document_edit(
            document_edit_id
        )
        return [r.to_json() for r in relations]


@ns.route("/<int:relation_id>")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationDeleteResource(RelationBaseRoute):

    @ns.doc(description="Delete a Relation by ID")
    def delete(self, relation_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_relation_accessible(user_id, relation_id)

        response = self.service.delete_relation_by_id(relation_id)
        return response

    @ns.expect(relation_update_input_dto)
    @ns.marshal_with(relation_output_model)
    @ns.doc(description="Update a Relation by ID")
    def patch(self, relation_id):
        data = request.get_json()
        schema_relation_id = data.get("schema_relation_id")
        mention_head_id = data.get("mention_head_id")
        mention_tail_id = data.get("mention_tail_id")

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_relation_accessible(user_id, relation_id)

        response = self.service.update_relation(
            relation_id,
            schema_relation_id,
            mention_head_id,
            mention_tail_id,
        )
        return response.to_json()


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class RelationCreationResource(RelationBaseRoute):

    @ns.doc(description="Create a new relation")
    @ns.marshal_with(relation_output_model)
    @ns.expect(relation_input_dto)
    def post(self):
        data = request.json

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, data["document_edit_id"]
        )

        response = self.service.create_relation(
            data.get("schema_relation_id"),
            data.get("document_edit_id"),
            data.get("mention_head_id"),
            data.get("mention_tail_id"),
        )
        return response.to_json()


@ns.route("/<int:relation_id>/accept")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(404, "Relation not found")
class RelationAcceptResource(RelationBaseRoute):

    @ns.marshal_with(relation_output_model)
    @ns.doc(description="Accept a relation by copying it and marking it as processed")
    def post(self, relation_id):
        """
        Accept a relation by copying it to the document edit and setting isShownRecommendation to False.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_relation_accessible(user_id, relation_id)

        return self.service.accept_relation(relation_id).to_json()


@ns.route("/<int:relation_id>/reject")
@ns.doc(params={"relation_id": "A Relation ID"})
@ns.response(404, "Relation not found")
class RelationRejectResource(RelationBaseRoute):

    @ns.doc(description="Reject a relation by marking it as processed")
    def post(self, relation_id):
        """
        Reject a relation by setting isShownRecommendation to False.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_relation_accessible(user_id, relation_id)

        return self.service.reject_relation(relation_id)
