from flask import request
from flask_restx import Namespace

from app.dtos import scope_create_input_dto
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.scope_service import scope_service, ScopeService
from app.dtos import scope_output_dto

ns = Namespace("scopes", description="Scope related operations")


class ScopeBaseRoute(AuthorizedBaseRoute):
    service: ScopeService = scope_service


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeQueryResource(ScopeBaseRoute):

    @ns.marshal_with(scope_output_dto)
    def get(self, document_edit_id):
        """
        Fetch scope tree of document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.get_scope_tree_by_document_edit_id(document_edit_id)
        return response

    @ns.expect(scope_create_input_dto)
    @ns.marshal_with(scope_output_dto)
    def post(self, document_edit_id):
        """
        Create a scope for a document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        data = request.get_json()

        response = self.service.create_scope(
            data.get("schema_scope_id"),
            data.get("token_start_id"),
            data.get("token_end_id"),
            document_edit_id,
            data.get("parent_scope_id"),
        )
        return response.to_json()
