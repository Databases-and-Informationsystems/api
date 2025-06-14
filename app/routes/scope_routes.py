from flask import request
from flask_restx import Namespace

from app.dtos import scope_create_input_dto
from app.file_logger import logger
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.scope_service import scope_service, ScopeService
from app.dtos import (
    scope_output_dto,
    scope_similarity_output_dto,
    scope_flat_output_dto,
)

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


@ns.route("/list/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeFlatQueryResource(ScopeBaseRoute):

    @ns.marshal_with(scope_flat_output_dto)
    def get(self, document_edit_id):
        """
        Fetch flat scope list of document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.get_scope_list_by_document_edit_id(document_edit_id)
        return response


@ns.doc(
    params={
        "model": {
            "description": f"AI model",
            "required": False,
        },
        "cache_datetime": {
            "description": f"Cache with datetime? (default: false)",
            "required": False,
        },
        "temperature": {
            "description": f"Temperature of the AI model",
            "required": False,
        },
        "with_text": {
            "description": f"Include the text in the prompt (only tokens otherwise)? (default: false)",
            "required": False,
        },
        "only_text": {
            "description": f"Only pass text instead of tokens to the llm? (default: false)",
            "required": False,
        },
    }
)
class ScopeRecommendationParamBaseRoute(ScopeBaseRoute):
    pass


@ns.route("/recommendation/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeRecommendationResource(ScopeRecommendationParamBaseRoute):

    @ns.marshal_with(scope_output_dto, as_list=True)
    @ns.doc(
        params={
            "only_leafs": {
                "description": "Shall only leafs be generated (default: false)?",
                "required": False,
            },
        },
        description="Executes the mention detection step.",
    )
    def post(self, document_edit_id):
        """
        Generate recommendations for scopes of a document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)
        logger.info(request.args)
        model = request.args.get("model")
        return self.service.get_scope_recommendations(
            document_edit_id, model, request.args
        )


@ns.route("/recommendation/branches/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeRecommendationResource(ScopeRecommendationParamBaseRoute):

    @ns.marshal_with(scope_output_dto, as_list=True)
    def post(self, document_edit_id):
        """
        Generate recommendations for scopes of a document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)
        logger.info(request.args)
        model = request.args.get("model")
        return self.service.get_scope_recommendations_branches(
            document_edit_id, model, request.args
        )


@ns.route("/similarity/<int:document_edit_id>/<int:compare_document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.doc(params={"compare_document_edit_id": "Document Edit ID to compare with"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeSimilarityResource(ScopeBaseRoute):

    @ns.marshal_with(scope_similarity_output_dto)
    def get(self, document_edit_id, compare_document_edit_id):
        """
        Compute scope tree similarity between two documents edits
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)
        response = self.service.scope_tree_similarity(
            document_edit_id, compare_document_edit_id
        )

        return response
