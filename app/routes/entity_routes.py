import typing
from flask_restx import Namespace

from app.models.buisness_models import BEntity
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.entity_service import entity_service, EntityService
from app.dtos import (
    entity_input_dto,
    entity_output_dto,
)
from flask import request

ns = Namespace("entities", description="Entity related operations")


class EntityBaseRoute(AuthorizedBaseRoute):
    service: EntityService = entity_service


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class EntityQueryResource(EntityBaseRoute):

    @ns.marshal_with(entity_output_dto, as_list=True)
    def get(self, document_edit_id):
        """
        Fetch all entities of a document annotation by its ID.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        entities: typing.List[BEntity] = self.service.get_entities_by_document_edit(
            document_edit_id
        )
        return [e.to_json() for e in entities]


@ns.route("/<int:entity_id>")
@ns.doc(params={"entity_id": "An Entity ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class EntityDeletionResource(EntityBaseRoute):

    @ns.doc(description="Delete an entity")
    def delete(self, entity_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_entity_accessible(user_id, entity_id)

        response = self.service.delete_entity(entity_id)
        return response


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class EntityCreationResource(EntityBaseRoute):

    @ns.doc(description="Create a new entity")
    @ns.marshal_with(entity_output_dto)
    @ns.expect(entity_input_dto)
    def post(self):
        data = request.json
        document_edit_id = data.get("document_edit_id")
        mention_ids = data.get("mention_ids")

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.create_entity(document_edit_id, mention_ids)
        return response
