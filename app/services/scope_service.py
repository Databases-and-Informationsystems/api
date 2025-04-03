import logging

from werkzeug.exceptions import BadRequest

from app.models import DocumentEdit
from app.repositories.scope_repository import ScopeRepository
from app.services.document_recommendation_service import (
    document_recommendation_service,
    DocumentRecommendationService,
)
from app.services.schema_scope_service import SchemaScopeService, schema_scope_service
from app.services.schema_service import SchemaService, schema_service
from app.services.token_service import TokenService, token_service


class ScopeService:
    __scope_repository: ScopeRepository
    token_service: TokenService
    schema_service: SchemaService
    schema_scope_service: SchemaScopeService
    document_recommendation_service: DocumentRecommendationService

    def __init__(
        self,
        scope_repository,
        token_service,
        schema_service,
        schema_scope_service,
        document_recommendation_service,
    ):
        self.__scope_repository = scope_repository
        self.token_service = token_service
        self.schema_service = schema_service
        self.schema_scope_service = schema_scope_service
        self.document_recommendation_service = document_recommendation_service

    def get_scope_tree_by_document_edit_id(self, document_edit_id):
        scope = self.__scope_repository.get_scope_tree_by_document_edit(
            document_edit_id
        )
        if not scope:
            raise BadRequest("Root Node does not exist")
        return scope.to_json()

    def create_scope(
        self,
        schema_scope_id,
        token_start_id,
        token_end_id,
        document_edit_id,
        parent_scope_id=None,
    ):
        # Check Tokens in document
        self.token_service.check_tokens_in_document_edit(
            [token_start_id, token_end_id], document_edit_id
        )

        # Check Scope Type is allowed
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_scope = self.schema_scope_service.get_schema_scope_by_id(schema_scope_id)
        if schema_scope.schema_id != schema.id:
            raise BadRequest("Scope Type not allowed")

        scope_tree = self.get_scope_tree_by_document_edit_id(document_edit_id)
        constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )
        if parent_scope_id is not None:
            parent = self.__get_scope_in_tree(scope_tree, parent_scope_id)
            if parent is None:
                raise BadRequest("Parent scope not part of document edit")
        else:
            parent = scope_tree
            parent_scope_id = parent["id"]

        self.__verify_tokens_non_overlapping(parent, token_start_id, token_end_id)

        self.__verify_schema_constraints(
            constraints, schema_scope_id, parent["schema_scope"]["id"]
        )

        return self.__scope_repository.create_scope(
            schema_scope_id,
            token_start_id,
            token_end_id,
            parent_scope_id,
            document_edit_id,
        )

    def __get_scope_in_tree(self, tree, scope_id):
        if tree is None:
            return None
        if tree["id"] == scope_id:
            return tree
        for child in tree["children"]:
            sub_tree = self.__get_scope_in_tree(child, scope_id)
            if sub_tree:
                return sub_tree
        return None

    def __verify_tokens_non_overlapping(self, parent, token_start_id, token_end_id):
        token_start = self.token_service.get_token_by_id(token_start_id).to_json()
        token_end = self.token_service.get_token_by_id(token_end_id).to_json()
        if token_start["document_index"] > token_end["document_index"]:
            raise BadRequest("Start token comes after the end token")
        if (
            parent["token_start"]["document_index"] > token_start["document_index"]
            or parent["token_end"]["document_index"] < token_end["document_index"]
        ):
            raise BadRequest("Tokens of scope exceed parent scope")
        for child in parent["children"]:
            if not (
                token_end["document_index"] < child["token_start"]["document_index"]
                or token_start["document_index"] > child["token_end"]["document_index"]
            ):
                raise BadRequest("Scope overlaps with other scope")

    def __verify_schema_constraints(
        self, constraints, child_schema_scope_id, parent_schema_scope_id
    ):
        for constraint in constraints:
            if (
                constraint["parent_type"]["id"] == parent_schema_scope_id
                and constraint["child_type"]["id"] == child_schema_scope_id
            ):
                return True
        raise BadRequest("No matching constraint found")

    def create_root_scope(self, document_edit_id, document_id, schema_id):
        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        max_token = tokens[0]
        min_token = tokens[0]
        for token in tokens:
            if token["document_index"] > max_token["document_index"]:
                max_token = token
            if token["document_index"] == 0:
                min_token = token
        schema_scope_root_id = (
            self.schema_scope_service.get_schema_scope_root_by_schema_id(schema_id).id
        )
        token_start_id = min_token["id"]
        token_end_id = max_token["id"]
        scope_tree = self.__scope_repository.get_scope_tree_by_document_edit(
            document_edit_id
        )
        if scope_tree:
            raise BadRequest("Root Node already exists")
        self.__scope_repository.create_scope(
            schema_scope_root_id,
            token_start_id,
            token_end_id,
            document_edit_id=document_edit_id,
        )

    def get_scope_recommendations(self, document_edit_id):
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )

        document_edit = self.__scope_repository.get_object_by_id(
            DocumentEdit, document_edit_id
        )
        tokens = self.token_service.get_tokens_by_document(document_edit.document.id)[
            "tokens"
        ]
        recommendations = self.document_recommendation_service.get_scope_recommendation(
            schema_scopes,
            schema_scope_constraints,
            document_edit.document.content,
            tokens,
            document_edit.document.id,
        )

        scopes = []
        for recommendation in recommendations:
            try:
                scopes.append(
                    self.create_scope(
                        recommendation["schema_scope_id"],
                        recommendation["token_start_id"],
                        recommendation["token_end_id"],
                        document_edit_id,
                        recommendation.get("parent_scope_id"),
                    )
                )
            except:
                logging.info("Failed to create scope: " + str(recommendation))
        return scopes


scope_service = ScopeService(
    ScopeRepository(),
    token_service,
    schema_service,
    schema_scope_service,
    document_recommendation_service,
)
