from flask_restx import Namespace
from app.dtos import token_output_list_dto
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.token_service import token_service, TokenService

ns = Namespace("tokens", description="Token related operations")


class TokenBaseRoute(AuthorizedBaseRoute):
    service: TokenService = token_service


@ns.route("/<int:document_id>")
@ns.doc(params={"document_id": "A Document ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TokenQueryResource(TokenBaseRoute):

    @ns.marshal_with(token_output_list_dto)
    def get(self, document_id):
        """
        Fetch tokens of document
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)

        response = self.service.get_tokens_by_document(document_id)
        return response
