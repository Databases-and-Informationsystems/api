from flask import request
from flask_restx import Namespace

from app.routes.base_routes import AuthorizedBaseRoute
from app.services.mention_services import mention_service, MentionService
from app.dtos import (
    mention_output_dto,
    mention_input_dto,
    mention_update_input_dto,
)

ns = Namespace("mentions", description="Mention related operations")


class MentionBaseRoute(AuthorizedBaseRoute):
    service: MentionService = mention_service


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class MentionResource(MentionBaseRoute):

    @ns.expect(mention_input_dto)
    @ns.marshal_with(mention_output_dto)
    def post(self):
        data = request.json

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, data["document_edit_id"]
        )

        return self.service.create_mention(
            data["document_edit_id"], data["schema_mention_id"], data["token_ids"]
        ).to_json()


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class MentionQueryResource(MentionBaseRoute):

    @ns.marshal_with(mention_output_dto, as_list=True)
    def get(self, document_edit_id):
        """
        Fetch all mentions of a document annotation by its ID.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        mentions = self.service.get_mentions_by_document_edit(document_edit_id)
        return [m.to_json() for m in mentions]


@ns.route("/<int:mention_id>")
@ns.doc(params={"mention_id": "A Mention ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class MentionDeletionResource(MentionBaseRoute):

    @ns.doc(description="Delete a mention and its related relations")
    def delete(self, mention_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_mention_accessible(user_id, mention_id)

        response = self.service.delete_mention(mention_id)
        return response

    @ns.expect(mention_update_input_dto)
    @ns.marshal_with(mention_output_dto)
    def patch(self, mention_id):
        """
        Update a mention by its ID.

        To remove entity ID from the mention, pass entity ID = 0.
        """
        data = request.get_json()
        schema_mention_id = data.get("schema_mention_id")
        token_ids = data.get("token_ids")
        entity_id = data.get("entity_id")

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_mention_accessible(user_id, mention_id)

        response = self.service.update_mention(
            mention_id, schema_mention_id, token_ids, entity_id
        )
        return response


@ns.route("/<int:mention_id>/accept")
@ns.doc(params={"mention_id": "A Mention ID"})
@ns.response(400, "Invalid input")
@ns.response(404, "Mention not found")
class MentionAcceptResource(MentionBaseRoute):

    @ns.doc(description="Accept a mention by copying it and marking it as processed")
    @ns.marshal_with(mention_output_dto)
    def post(self, mention_id):
        """
        Accept a mention by copying it to the document edit and setting isShownRecommendation to False.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_mention_accessible(user_id, mention_id)

        return self.service.accept_mention(mention_id)


@ns.route("/<int:mention_id>/reject")
@ns.doc(params={"mention_id": "A Mention ID"})
@ns.response(400, "Invalid input")
@ns.response(404, "Mention not found")
class MentionRejectResource(MentionBaseRoute):

    @ns.doc(description="Reject a mention by marking it as processed")
    def post(self, mention_id):
        """
        Reject a mention by setting isShownRecommendation to False.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_mention_accessible(user_id, mention_id)

        return self.service.reject_mention(mention_id)
