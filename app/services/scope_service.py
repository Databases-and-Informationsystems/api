import logging
from collections import defaultdict

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

    def get_scope_recommendations(self, document_edit_id, model, step):
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

        if step == "top-level":
            schema_scopes = [
                schema_scope_constraint["child_type"]
                for schema_scope_constraint in schema_scope_constraints
                if schema_scope_constraint["parent_type"]["type"] == "root"
            ]

        elif step == "subtrees":
            toplevel_schema_scopes = [
                schema_scope_constraint["child_type"]
                for schema_scope_constraint in schema_scope_constraints
                if schema_scope_constraint["parent_type"]["type"] == "root"
            ]
            schema_scopes = [
                schema_scope
                for schema_scope in schema_scopes
                if any(
                    schema_scope_constraint["parent_type"]["type"] != "root"
                    and schema_scope_constraint["child_type"]["type"]
                    == schema_scope["type"]
                    for schema_scope_constraint in schema_scope_constraints
                )
            ]
            tree = self.get_scope_tree_by_document_edit_id(document_edit.id)

            relevant_schema_scopes = [
                tss["type"]
                for tss in toplevel_schema_scopes
                if any(
                    schema_scope_constraint["parent_type"]["type"] == tss["type"]
                    for schema_scope_constraint in schema_scope_constraints
                )
            ]

            relevant_token_list = []

            if tree["children"]:
                for child in tree["children"]:
                    if child["schema_scope"]["type"] in relevant_schema_scopes:
                        relevant_token_list.extend(
                            tokens[
                                child["token_start"]["document_index"] : child[
                                    "token_end"
                                ]["document_index"]
                            ]
                        )
            tokens = relevant_token_list

        recommendations = self.document_recommendation_service.get_scope_recommendation(
            schema_scopes,
            schema_scope_constraints,
            document_edit.document.content,
            tokens,
            document_edit.document.id,
            model,
        )

        postprocessed_recommendations = self.__postprocess_scope_tree(
            recommendations, tokens, schema_scopes, schema_scope_constraints
        )
        scopes = []
        scope_id_mapping = {}
        root = self.get_scope_tree_by_document_edit_id(document_edit_id)
        scope_id_mapping[None] = root["id"]
        for recommendation in postprocessed_recommendations:
            try:
                if recommendation["schema_scope_id"] == root["schema_scope"]["id"]:
                    scope_id_mapping[recommendation["id"]] = root["id"]
                else:
                    new_scope = self.create_scope(
                        recommendation["schema_scope_id"],
                        recommendation["token_start_id"],
                        recommendation["token_end_id"],
                        document_edit_id,
                        scope_id_mapping[recommendation.get("parent_scope_id")],
                    )
                    scopes.append(new_scope)
                    scope_id_mapping[recommendation["id"]] = new_scope.id
            except Exception as e:
                logging.info(
                    "Failed to create scope: " + str(recommendation) + ", " + str(e)
                )
        return self.get_scope_tree_by_document_edit_id(document_edit_id)

    def __postprocess_scope_tree(
        self, scope_recommendations, tokens, schema_scopes, schema_scope_constraints
    ):
        merged_scopes = []
        schema_scope_dict = dict()
        for schema_scope in schema_scopes:
            schema_scope_dict[schema_scope["type"]] = schema_scope["id"]

        token_index_dict = dict()
        for token in tokens:
            token_index_dict[token["document_index"]] = token["id"]

        merging_allowed = dict()
        for schema_scope_constraint in schema_scope_constraints:
            merging_allowed[
                (
                    schema_scope_constraint["parent_type"]["type"],
                    schema_scope_constraint["child_type"]["type"],
                )
            ] = schema_scope_constraint["merge_consecutive_children"]
        merged_scope_id_mapping = dict()
        parent_children_dict = defaultdict(list)
        parent_type_dict = {None: "root"}

        for scope_recommendation in scope_recommendations:  # Group by parent id
            parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                scope_recommendation
            )
            parent_type_dict[scope_recommendation["id"]] = scope_recommendation[
                "scope_type"
            ]

        for key in parent_children_dict:
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["startTokenDocumentIndex"],
            )
            merged = parent_children_dict[key][0]
            merged_scope_id_mapping[merged["id"]] = merged["id"]

            if len(parent_children_dict[key]) == 1:
                merged_scopes.append(merged)
            else:
                for scope in parent_children_dict[key][1:]:
                    if (
                        merging_allowed.get(
                            (parent_type_dict.get(key), scope["scope_type"])
                        )
                        and scope["scope_type"] == merged["scope_type"]
                        and scope["startTokenDocumentIndex"]
                        == merged["endTokenDocumentIndex"] + 1
                    ):
                        merged_scope_id_mapping[scope["id"]] = merged["id"]
                        merged = {
                            "id": merged["id"],
                            "scope_type": merged["scope_type"],
                            "startTokenDocumentIndex": merged[
                                "startTokenDocumentIndex"
                            ],
                            "endTokenDocumentIndex": scope["endTokenDocumentIndex"],
                            "parent_scope_id": merged["parent_scope_id"],
                        }
                    else:
                        merged_scopes.append(merged)
                        merged = scope
                        merged_scope_id_mapping[merged["id"]] = merged["id"]

                merged_scopes.append(merged)
        for merged_scope in merged_scopes:
            merged_scope["id"] = merged_scope_id_mapping[merged_scope["id"]]
            merged_scope["parent_scope_id"] = merged_scope_id_mapping.get(
                merged_scope["parent_scope_id"]
            )
            merged_scope["schema_scope_id"] = schema_scope_dict[
                merged_scope["scope_type"]
            ]
            merged_scope["token_start_id"] = token_index_dict[
                merged_scope["startTokenDocumentIndex"]
            ]
            merged_scope["token_end_id"] = token_index_dict[
                merged_scope["endTokenDocumentIndex"]
            ]

        merged_scopes = self.__merge_equal_scopes(merged_scopes)
        logging.info(merged_scopes)
        return sorted(merged_scopes, key=lambda x: x["id"])

    def __merge_equal_scopes(self, merged_scopes):
        scope_id_dict = dict()
        parent_children_dict = defaultdict(list)
        for merged_scope in merged_scopes:
            parent_children_dict[merged_scope["parent_scope_id"]].append(merged_scope)
            scope_id_dict[merged_scope["id"]] = merged_scope

        # Merge child with parent if type and bounds are equal
        for key in parent_children_dict:
            if len(parent_children_dict[key]) != 1 or key is None:
                continue
            scope = parent_children_dict[key][0]
            if scope_id_dict[key]["scope_type"] != scope["scope_type"]:
                continue

            if (
                scope_id_dict[key]["startTokenDocumentIndex"]
                == scope["startTokenDocumentIndex"]
                and scope_id_dict[key]["endTokenDocumentIndex"]
                == scope["endTokenDocumentIndex"]
            ):
                for child_scope in parent_children_dict[scope["id"]]:
                    child_scope["parent_scope_id"] = scope["parent_scope_id"]
                merged_scopes = [s for s in merged_scopes if s["id"] != scope["id"]]
        return merged_scopes


scope_service = ScopeService(
    ScopeRepository(),
    token_service,
    schema_service,
    schema_scope_service,
    document_recommendation_service,
)
