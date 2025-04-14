from flask import current_app
from werkzeug.exceptions import BadRequest
import requests
import logging

from app.repositories.document_recommendation_repository import (
    DocumentRecommendationRepository,
)
from app.services.mention_services import MentionService, mention_service
from app.services.schema_service import schema_service, SchemaService
from app.services.token_service import token_service, TokenService
from app.services.relation_services import relation_service, RelationService
from app.services.entity_service import entity_service, EntityService


class DocumentRecommendationService:
    __document_recommendation_repository: DocumentRecommendationRepository
    mention_service: MentionService
    token_service: TokenService
    schema_service: SchemaService
    relation_service: RelationService
    entity_service: EntityService

    def __init__(
        self,
        document_recommendation_repository,
        mention_service,
        token_service,
        schema_service,
        relation_service,
        entity_service,
    ):
        self.__document_recommendation_repository = document_recommendation_repository
        self.mention_service = mention_service
        self.token_service = token_service
        self.schema_service = schema_service
        self.relation_service = relation_service
        self.entity_service = entity_service

    def create_document_recommendation(self, document_id=None, document_edit_id=None):
        return self.__document_recommendation_repository.create_document_recommendation(
            document_id, document_edit_id
        )

    def get_mention_recommendation(self, document_id, schema_id, content, params):
        # get schema_mention
        schema_mentions = self.schema_service.get_schema_mentions_by_schema(schema_id)
        if schema_mentions is None:
            raise BadRequest("Schema mentions not found")

        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        if tokens is None:
            raise BadRequest("Tokens not found")

        mention_recommendation_input = self.get_mention_recommendation_input_dto(
            tokens, schema_id, schema_mentions, content, document_id
        )

        # get mention_recommendation from pipeline service
        mention_recommendations = self.get_mention_recommendation_from_pipeline_service(
            mention_recommendation_input, params=params
        )

        # check for duplicate and overlapping tokens
        if not self.no_overlapping_or_duplicate_tokens(mention_recommendations):
            raise BadRequest("Overlapping or duplicate mentions found")

        # create id tag dictionary for schema_mention
        schema_mention_dict = dict()
        for schema_mention in schema_mentions:
            schema_mention_dict[schema_mention.tag] = schema_mention.id

        # create dictionary with filtered token ids belonging to a mention along with tag
        filtered_token_ids_and_schema_mention_id = (
            self.filter_tokens_by_schema_recommendations(
                tokens,
                mention_recommendations,
                schema_mention_dict,
            )
        )

        return filtered_token_ids_and_schema_mention_id

    def get_mention_recommendation_from_pipeline_service(
        self, mention_recommendation_input, params
    ):
        # get request dto for pipeline service

        # Define the base URL
        url = current_app.config.get("PIPELINE_URL") + "/steps/mention"
        # Define the headers
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.post(
            url, params=params, json=mention_recommendation_input, headers=headers
        )
        if response.status_code != 200:
            raise BadRequest("Failed to fetch recommendations: " + response.text)
        mention_recommendations = response.json()
        return mention_recommendations

    def get_mention_recommendation_input_dto(
        self, tokens, schema_id, schema_mentions, content, document_id
    ):
        schema_mention_recommendation_input = (
            self.get_schema_mention_recommendation_input_dto(schema_mentions)
        )

        return {
            "document_id": str(document_id),
            "schema": {
                "id": schema_id,
                "schema_mentions": schema_mention_recommendation_input,
            },
            "content": content,
            "tokens": tokens,
        }

    def get_schema_mention_recommendation_input_dto(self, schema_mentions):
        return [
            {
                "id": schema_mention.id,
                "tag": schema_mention.tag,
                "description": schema_mention.description,
            }
            for schema_mention in schema_mentions
        ]

    def no_overlapping_or_duplicate_tokens(self, tokens):

        # Sort tokens by their start index
        sorted_tokens = sorted(tokens, key=lambda x: x["startTokenDocumentIndex"])

        # Check for tokens with the same start and end index
        for token in sorted_tokens:
            if token["startTokenDocumentIndex"] > token["endTokenDocumentIndex"]:
                return False  # Token with higher start than end index found

        # Iterate through the sorted tokens and check for overlaps
        for i in range(len(sorted_tokens) - 1):
            current_token = sorted_tokens[i]
            next_token = sorted_tokens[i + 1]

            # Check if the current token overlaps with the next token
            if (
                current_token["endTokenDocumentIndex"]
                >= next_token["startTokenDocumentIndex"]
            ):
                return False  # Overlap found

        return True  # No overlaps or duplicate tokens found

    def filter_tokens_by_schema_recommendations(
        self, tokens, mention_recommendations, schema_mention_dict
    ):
        result = []

        for mention_recommendations_item in mention_recommendations:
            start = mention_recommendations_item["startTokenDocumentIndex"]
            end = mention_recommendations_item["endTokenDocumentIndex"]
            type_ = mention_recommendations_item["type"]

            # Filter tokens whose document_index is between start and end (inclusive)
            filtered_token_ids = [
                token["id"]
                for token in tokens
                if start <= token["document_index"] <= end
            ]

            # Append the result with the type and filtered tokens
            if len(filtered_token_ids) > 0:
                result.append(
                    {
                        "mention_schema_id": schema_mention_dict[type_],
                        "token_ids": filtered_token_ids,
                    }
                )

        return result

    def get_relation_recommendation(
        self, document_edit_id, schema_id, content, document_id, params
    ):
        schema = self.schema_service.get_schema_by_id(schema_id)
        mentions_data = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )

        relation_recommendation_input = self.get_relation_recommendation_input_dto(
            content,
            mentions_data["mentions"],
            document_id,
            schema,
        )

        relations_recommendations = (
            self.get_relation_recommendation_from_pipeline_service(
                relation_recommendation_input, params
            )
        )
        schema_relations_dict = dict()
        for schema_relation in schema["schema_relations"]:
            schema_relations_dict[schema_relation["tag"]] = schema_relation["id"]

        mention_id_to_schema_mention_id = dict()
        for mention in mentions_data["mentions"]:
            mention_id_to_schema_mention_id[mention["id"]] = mention["schema_mention"][
                "id"
            ]

        document_recommendation = self.__document_recommendation_repository.get_document_recommendation_by_document_edit(
            document_edit_id
        )

        if document_recommendation is None:
            raise BadRequest("Document recommendation not found")

        constraints = []
        for relation in relations_recommendations:
            try:
                constraints.append(
                    self.schema_service.verify_constraint(
                        schema,
                        schema_relation_id=schema_relations_dict[relation["tag"]],
                        head_schema_mention_id=mention_id_to_schema_mention_id[
                            relation["head_mention_id"]
                        ],
                        tail_schema_mention_id=mention_id_to_schema_mention_id[
                            relation["tail_mention_id"]
                        ],
                    )
                )
            except:
                constraints.append(None)

        for relation, constraint in zip(relations_recommendations, constraints):
            if constraint is not None:
                self.relation_service.save_relation_in_edit(
                    schema_relation_id=schema_relations_dict[relation["tag"]],
                    is_directed=constraint["is_directed"],
                    mention_head_id=relation["head_mention_id"],
                    mention_tail_id=relation["tail_mention_id"],
                    document_edit_id=document_edit_id,
                    document_recommendation_id=document_recommendation.id,
                    is_shown_recommendation=True,
                )

    def get_relation_recommendation_from_pipeline_service(
        self, relation_recommendation_input, params
    ):

        url = current_app.config.get("PIPELINE_URL") + "/steps/relation"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        logging.debug(f"Sending request to pipeline: {url}")
        logging.debug(f"Payload: {relation_recommendation_input}")
        logging.debug(f"Params: {params}")
        response = requests.post(
            url, params=params, json=relation_recommendation_input, headers=headers
        )
        logging.debug(f"Pipeline Response Status: {response.status_code}")
        logging.debug(f"Pipeline Response Text: {response}")
        if response.status_code != 200:
            raise BadRequest(
                "Failed to fetch relation recommendations: " + response.text
            )
        relation_recommendations = response.json()
        logging.debug(f"Pipeline Response JSON: {relation_recommendations}")
        return relation_recommendations

    def get_relation_recommendation_input_dto(
        self,
        content,
        mentions,
        document_id,
        schema,
    ):
        return {
            "document_id": str(document_id),
            "schema": schema,
            "content": content,
            "mentions": mentions,
        }

    def get_entity_recommendation(
        self, document_edit_id, schema_id, content, document_id, params
    ):
        schema = self.schema_service.get_schema_by_id(schema_id)
        mentions_data = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )
        entity_possible_dict = {}
        for mention in mentions_data["mentions"]:
            entity_possible_dict[mention["id"]] = mention["schema_mention"][
                "entityPossible"
            ]

        entity_recommendation_input = self.get_entity_recommendation_input_dto(
            content,
            mentions_data["mentions"],
            document_id,
            schema,
        )

        entity_recommendations = self.get_entity_recommendation_from_pipeline_service(
            entity_recommendation_input, params
        )

        document_recommendation = self.__document_recommendation_repository.get_document_recommendation_by_document_edit(
            document_edit_id
        )

        for mention_group in entity_recommendations:
            mention_list = mention_group.get("mentions", [])
            for mention in mention_list:
                if (
                    mention["id"] not in entity_possible_dict.keys()
                    or entity_possible_dict[mention["id"]] == False
                ):
                    mention_list.remove(mention)
            if len(mention_list) > 0:
                self.entity_service.save_entity_in_edit(
                    document_edit_id, mention_list, document_recommendation.id
                )

    def get_entity_recommendation_input_dto(
        self,
        content,
        mentions,
        document_id,
        schema,
    ):

        return {
            "document_id": str(document_id),
            "schema": {
                "id": schema["id"],
                "schema_mentions": schema["schema_mentions"],
            },
            "content": content,
            "mentions": mentions,
        }

    def get_entity_recommendation_from_pipeline_service(
        self, entity_recommendation_input, params
    ):

        url = current_app.config.get("PIPELINE_URL") + "/steps/entity"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.post(
            url, params=params, json=entity_recommendation_input, headers=headers
        )

        if response.status_code != 200:
            raise BadRequest("Failed to fetch entity recommendations: " + response.text)
        entity_recommendations = response.json()
        return entity_recommendations

    def get_scope_recommendation(
        self,
        schema_scopes,
        schema_scope_constraints,
        content,
        tokens,
        document_id=None,
        model=None,
    ):
        url = current_app.config.get("SCOPE_URL") + "/scopes"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        json_input = {
            "document_id": str(document_id) if document_id else None,
            "schema": {
                "schema_scopes": schema_scopes,
                "schema_scope_constraints": schema_scope_constraints,
            },
            "content": content,
            "tokens": tokens,
        }
        response = requests.post(
            url, json=json_input, headers=headers, params={"model": model}
        )
        if response.status_code != 200:
            raise BadRequest("Failed to fetch scope recommendations: " + response.text)
        scope_recommendations = response.json()

        # check for duplicate and overlapping tokens
        if not self.no_overlapping_or_duplicate_tokens(scope_recommendations):
            raise BadRequest("Overlapping or duplicate scopes found")

        schema_scope_dict = dict()
        for schema_scope in schema_scopes:
            schema_scope_dict[schema_scope["type"]] = schema_scope["id"]

        token_index_dict = dict()
        for token in tokens:
            token_index_dict[token["document_index"]] = token["id"]

        scopes = [
            {
                "schema_scope_id": schema_scope_dict[
                    scope_recommendation["scope_type"]
                ],
                "token_start_id": token_index_dict[
                    scope_recommendation["startTokenDocumentIndex"]
                ],
                "token_end_id": token_index_dict[
                    scope_recommendation["endTokenDocumentIndex"]
                ],
                "parent_scope_id": None,
            }
            for scope_recommendation in scope_recommendations
        ]
        return scopes


document_recommendation_service = DocumentRecommendationService(
    DocumentRecommendationRepository(),
    mention_service,
    token_service,
    schema_service,
    relation_service,
    entity_service,
)
