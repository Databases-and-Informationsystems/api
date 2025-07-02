import copy
import json
import logging
import os
from datetime import datetime

from werkzeug.exceptions import BadRequest, NotFound

from app.repositories.document_edit_repository import DocumentEditRepository
from app.services.document_recommendation_service import (
    DocumentRecommendationService,
    document_recommendation_service,
)
from app.services.entity_service import EntityService, entity_service
from app.services.f1_score_service import f1_score_service, F1ScoreService
from app.services.schema_scope_service import schema_scope_service, SchemaScopeService
from app.services.schema_service import SchemaService, schema_service
from app.services.scope_service import ScopeService, scope_service
from app.services.token_service import TokenService, token_service
from app.services.mention_services import MentionService, mention_service
from app.services.relation_services import RelationService, relation_service


class DocumentEditService:
    __document_edit_repository: DocumentEditRepository
    document_recommendation_service: DocumentRecommendationService
    token_service: TokenService
    mention_service: MentionService
    relation_service: RelationService
    schema_service: SchemaService
    entity_service: EntityService
    f1_score_service: F1ScoreService
    scope_service: ScopeService
    schema_scope_service: SchemaScopeService

    def __init__(
        self,
        document_edit_repository,
        document_recommendation_service,
        token_service,
        mention_service,
        relation_service,
        schema_service,
        entity_service,
        f1_score_service,
        scope_service,
        schema_scope_service,
    ):
        self.__document_edit_repository = document_edit_repository
        self.document_recommendation_service = document_recommendation_service
        self.token_service = token_service
        self.mention_service = mention_service
        self.relation_service = relation_service
        self.schema_service = schema_service
        self.entity_service = entity_service
        self.f1_score_service = f1_score_service
        self.scope_service = scope_service
        self.schema_scope_service = schema_scope_service

    def create_document_edit(
        self,
        user_id,
        document_id,
        model_mention=None,
        model_entities=None,
        model_relation=None,
        model_settings_mention=None,
        model_settings_entities=None,
        model_settings_relation=None,
        with_recommendations=True,
    ):
        """
        Create a new document annotation.
        Generates recommendations for mentions and stores them for the newly created annotation.

        [Optional] takes ids and settings of models available inside the schema for mention, entity and relation suggestion.
        If not specified, default models (LLM) and default settings are used.

        :param user_id: Owner ID of new annotation.
        :param document_id: Document ID to which the annotation belongs.
        :param model_mention: ID of model to use for mention recommendations.
        :param model_entities: ID of model to use for entity recommendations.
        :param model_relation: ID of model to use for relation recommendations.
        :param model_settings_mention: Settings for mention recommendations as dict with fields "key" and "value".
        :param model_settings_entities: Settings for entity recommendations as dict with fields "key" and "value".
        :param model_settings_relation: Settings for relation recommendations as dict with fields "key" and "value".
        :param with_recommendations: If true, create recommendations for mentions.
        :return: document_edit_output_dto
        :raises BadRequest: If annotation already exists, invalid model IDs were given or recommendation generation fails.
        """
        # Check if document edit already exists
        # existing_doc_edit = self.__get_document_edit_by_document(document_id, user_id)
        # if existing_doc_edit is not None:
        #    raise BadRequest("Document Edit already exists")

        # Get schema of document
        schema = self.schema_service.get_schema_by_document(document_id)

        # Use default llm if no model is specified
        if not all([model_mention, model_relation, model_entities]):
            models = self.schema_service.get_models_by_schema(schema.id)
            models = [
                model
                for model in models
                if model["name"] == "OpenAI Large Language Model"
            ]
            if model_mention is None:
                for model in models:
                    if model["step"]["id"] == 1:
                        model_mention = model["id"]
            if model_entities is None:
                for model in models:
                    if model["step"]["id"] == 2:
                        model_entities = model["id"]
            if model_relation is None:
                for model in models:
                    if model["step"]["id"] == 3:
                        model_relation = model["id"]

        # Verify models are valid for given schema and steps
        self.schema_service.check_models_in_schema(
            model_mention, model_entities, model_relation, schema.id
        )

        # Create document edit
        document_edit = self.__document_edit_repository.create_document_edit(
            document_id,
            user_id,
            schema.id,
            model_mention,
            model_entities,
            model_relation,
        )
        doc_edit = self.__get_document_edit_with_document_by_id(document_edit.id)

        # Create document recommendation for document edit
        document_recommendation = (
            self.document_recommendation_service.create_document_recommendation(
                document_edit_id=document_edit.id, document_id=document_id
            )
        )

        # Store model settings
        self.__document_edit_repository.store_model_settings(
            document_edit.id, model_mention, model_settings_mention
        )
        self.__document_edit_repository.store_model_settings(
            document_edit.id, model_entities, model_settings_entities
        )
        self.__document_edit_repository.store_model_settings(
            document_edit.id, model_relation, model_settings_relation
        )

        # Create mention recommendations
        # if with_recommendations:
        #    params = self.__get_recommendation_params(document_edit.id, 1)  # MENTIONS
        #    mention_recommendations = (
        #        self.document_recommendation_service.get_mention_recommendation(
        #            document_id, doc_edit.schema_id, doc_edit.content, params
        #        )
        #    )

        #    # Store mention recommendations
        #    self.mention_service.create_recommended_mention(
        #        document_edit.id, document_recommendation.id, mention_recommendations
        #    )

        # Create Root Scope
        self.scope_service.create_root_scope(document_edit.id, document_id, schema.id)

        return {
            "id": document_edit.id,
            "schema_id": document_edit.schema_id,
            "document_id": document_edit.document_id,
            "mention_model_id": document_edit.mention_model_id,
            "entity_model_id": document_edit.entity_model_id,
            "relation_model_id": document_edit.relation_model_id,
            "state": {"id": 5, "state": "MENTION_SUGGESTION"},
        }

    def __get_document_edit_by_document(self, document_id, user_id):
        """
        Fetch DocumentEdit database entry by document ID and user ID.

        :param document_id: Document ID to which the annotation belongs.
        :param user_id: User ID to which the annotation belongs.
        :return: DocumentEdit database entry.
        """
        return self.__document_edit_repository.get_document_edit_by_document(
            document_id, user_id
        )

    def __get_document_edit_with_document_by_id(self, document_edit_id):
        """
        Fetch DocumentEdit database entry with document information by document edit ID.

        :param document_edit_id: Document ID to which the annotation belongs.
        :return: DocumentEdit database entry with document information.
        """
        return self.__document_edit_repository.get_document_edit_with_document_by_id(
            document_edit_id
        )

    def overtake_document_edit(self, logged_in_user_id, document_edit_id):
        document_edit = self.__document_edit_repository.get_document_edit_by_id(
            document_edit_id
        )
        if document_edit is None:
            raise NotFound("Document edit does not exist")

        current_owner_id = document_edit.user_id

        if logged_in_user_id == current_owner_id:
            raise BadRequest("User already has access to this document edit")
        # check for team

        # check if another document edit exist for current user
        existing_document_edit = self.__get_document_edit_by_document(
            document_edit.document_id, logged_in_user_id
        )
        if existing_document_edit is not None:
            raise BadRequest("Document edit already exists")

        document_edit.user_id = logged_in_user_id

        # save
        self.__document_edit_repository.store_object(document_edit)

        return {
            "id": document_edit.id,
            "schema_id": document_edit.schema_id,
            "document_id": document_edit.document_id,
            "mention_model_id": document_edit.mention_model_id,
            "entity_model_id": document_edit.entity_model_id,
            "relation_model_id": document_edit.relation_model_id,
            "state": {
                "id": document_edit.state_id,
                "state": document_edit.state_name,
            },
        }

    def soft_delete_document_edit(self, document_edit_id):
        if not isinstance(document_edit_id, int) or document_edit_id <= 0:
            raise BadRequest("Invalid document edit ID. Must be a positive integer.")

        success = self.__document_edit_repository.soft_delete_document_edit(
            document_edit_id
        )
        if not success:
            raise NotFound("DocumentEdit not found or already inactive.")
        return {"message": "DocumentEdit set to inactive successfully."}

    def soft_delete_edits_for_document(self, document_id):
        self.__document_edit_repository.soft_delete_document_edits_by_document_id(
            document_id
        )

    def bulk_soft_delete_edits_for_documents(self, document_ids: list[int]):
        if not document_ids:
            return
        self.__document_edit_repository.bulk_soft_delete_edits(document_ids)

    def get_document_edit_by_id(self, document_edit_id):
        """
        Fetch DocumentEdit object with associated mentions and relations.

        :param document_edit_id: DocumentEdit ID of the annotation.
        :return: finished_document_edit_output_dto
        :raises NotFound: If DocumentEdit does not exist.
        """
        document_edit = self.__document_edit_repository.get_document_edit_by_id(
            document_edit_id
        )
        if document_edit is None:
            raise NotFound("Document Edit doesnt exist")

        tokens_data = self.token_service.get_tokens_by_document(
            document_edit.document_id
        )
        tokens = tokens_data.get("tokens", [])
        mentions_data = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )
        relations_data = self.relation_service.get_relations_by_document_edit(
            document_edit_id
        )
        return {
            "document": {
                "id": document_edit.document_id,
                "tokens": tokens,
            },
            "schema_id": document_edit.schema_id,
            "mentions": mentions_data["mentions"],
            "relations": relations_data["relations"],
            "state": {
                "id": document_edit.state_id,
                "state": document_edit.state_name,
            },
        }

    def get_document_edit_by_id_for_difference_calc(self, document_edit_id):
        document_edit = self.__document_edit_repository.get_document_edit_by_id(
            document_edit_id
        )
        if document_edit is None:
            raise NotFound("Document Edit doesnt exist")

        tokens_data = self.token_service.get_tokens_by_document(
            document_edit.document_id
        )
        tokens = tokens_data.get("tokens", [])
        mentions_data = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )

        non_recommended_mentions_dict = [
            mention
            for mention in mentions_data.get("mentions", [])
            if mention["document_recommendation_id"] is None
        ]

        transformed_mentions = [
            {
                "tag": mention["tag"],
                "tokens": mention["tokens"],
                **(
                    {"entity": {"id": mention["entity_id"]}}
                    if mention.get("entity_id")
                    else {}
                ),  # Only add entity object if entity_id exists
            }
            for mention in non_recommended_mentions_dict
        ]
        relations_data = self.relation_service.get_relations_by_document_edit(
            document_edit_id
        )

        non_recommended_relations_dict = [
            relation
            for relation in relations_data.get("relations", [])
            if relation["document_recommendation_id"] is None
        ]

        transformed_relations = [
            {
                "tag": relation["tag"],
                "mention_head": {
                    "tag": relation["head_mention"]["tag"],
                    "tokens": relation["head_mention"]["tokens"],
                    **(
                        {"entity": {"id": relation["head_mention"]["entity_id"]}}
                        if relation["head_mention"].get("entity_id")
                        else {}
                    ),  # Only add entity object if entity_id exists
                },
                "mention_tail": {
                    "tag": relation["tail_mention"]["tag"],
                    "tokens": relation["tail_mention"]["tokens"],
                    **(
                        {"entity": {"id": relation["tail_mention"]["entity_id"]}}
                        if relation["tail_mention"].get("entity_id")
                        else {}
                    ),  # Only add entity object if entity_id exists
                },
            }
            for relation in non_recommended_relations_dict
        ]

        return {
            "document": {
                "id": document_edit.document_id,
                "tokens": tokens,
            },
            "schema_id": document_edit.schema_id,
            "mentions": transformed_mentions,
            "relations": transformed_relations,
        }

    def get_document_edit_model(self, document_edit_id):
        """
        Fetch selected models with associated settings chosen for given DocumentEdit.

        :param document_edit_id: DocumentEdit ID of the annotation.
        :return: document_edit_model_output_list_dto
        """
        settings = self.__document_edit_repository.get_document_edit_model(
            document_edit_id
        )
        model_dict = {}
        for setting in settings:
            if setting.id not in model_dict:
                model_dict[setting.id] = {
                    "document_edit_id": setting.document_edit_id,
                    "id": setting.id,
                    "name": setting.model_name,
                    "type": setting.model_type,
                    "step": {
                        "id": setting.model_step_id,
                        "type": setting.model_step_name,
                    },
                    "settings": [],
                }

            if setting.settings_id is not None:
                model_dict[setting.id]["settings"].append(
                    {
                        "id": setting.settings_id,
                        "value": setting.value,
                        "key": setting.key,
                    }
                )
        return {"models": list(model_dict.values())}

    def save_relation_recommendation(self, document_edit_id):
        """
        Generate and save relation recommendations for given DocumentEdit.

        :param document_edit_id: DocumentEdit ID of the annotation.
        :raises BadRequest: If recommendation generation fails.
        """
        doc_edit = self.__get_document_edit_with_document_by_id(document_edit_id)
        params = self.__get_recommendation_params(document_edit_id, 3)  # RELATIONS
        self.document_recommendation_service.get_relation_recommendation(
            document_edit_id,
            doc_edit.schema_id,
            doc_edit.content,
            doc_edit.document_id,
            params,
        )

    def save_entity_recommendation(self, document_edit_id):
        """
        Generate and save entity recommendations for given DocumentEdit.

        :param document_edit_id: DocumentEdit ID of the annotation.
        :raises BadRequest: If recommendation generation fails.
        """
        doc_edit = self.__get_document_edit_with_document_by_id(document_edit_id)
        params = self.__get_recommendation_params(document_edit_id, 2)  # ENTITIES
        self.document_recommendation_service.get_entity_recommendation(
            document_edit_id,
            doc_edit.schema_id,
            doc_edit.content,
            doc_edit.document_id,
            params,
        )

    def __get_recommendation_params(self, document_edit_id, step_id):
        """
        Fetch model data and settings to pass in query for recommendation generation.

        :param document_edit_id: DocumentEdit ID of the annotation.
        :param step_id: Step of the model. 1 = MENTIONS, 2 = ENTITIES, 3 = RELATIONS
        :return: Query parameters to pass in recommendation system
        """
        params = {}
        models = self.get_document_edit_model(document_edit_id)["models"]
        for model in models:
            if model["step"]["id"] == step_id:
                params["model_type"] = model["type"]
                params["name"] = model["name"]
                for setting in model["settings"]:
                    params[setting["key"]] = setting["value"]
        return params

    def set_edit_state(self, document_edit_id, state_name):
        """
        Set Edit State of a document edit to another step.
        Possible is only the directly following step.

        When proceeding to a suggestion step, new recommendations will be generated.
        If unreviewed recommendations exist, it is forbidden to leave the suggestion step.

        :param document_edit_id: DocumentEdit ID
        :param state_name: New state of the document edit
        :return: document_edit_output_dto
        :raises NotFound: If document edit does not exist
        :raises BadRequest: If it is not allowed to proceed to specified step.
        """
        state = self.__document_edit_repository.get_state_by_name(state_name)
        if state is None:
            raise BadRequest("Invalid state")
        document_edit = self.__document_edit_repository.get_document_edit_by_id(
            document_edit_id
        )
        if document_edit is None:
            raise NotFound("Document edit does not exist")

        if document_edit.state_name == "MENTION_SUGGESTION":
            if state_name != "MENTIONS":
                raise BadRequest("Not allowed to proceed to this step")
            recs = self.mention_service.get_recommendations_by_document_edit(
                document_edit_id
            )
            if len(recs) != 0:
                raise BadRequest("Unreviewed recommendations left")
        elif document_edit.state_name == "MENTIONS":
            if state_name != "ENTITIES":
                raise BadRequest("Not allowed to proceed to this step")

            self.save_entity_recommendation(document_edit_id)
            self.entity_service.create_entity_for_mentions(document_edit_id)

        elif document_edit.state_name == "ENTITIES":
            if state_name != "RELATION_SUGGESTION":
                raise BadRequest("Not allowed to proceed to this step")

            self.save_relation_recommendation(document_edit_id)

        elif document_edit.state_name == "RELATION_SUGGESTION":
            if state_name != "RELATIONS":
                raise BadRequest("Not allowed to proceed to this step")
            recs = self.relation_service.get_recommendations_by_document_edit(
                document_edit_id
            )
            if len(recs) != 0:
                raise BadRequest("Unreviewed recommendations left")
        elif document_edit.state_name == "RELATIONS":
            if state_name != "FINISHED":
                raise BadRequest("Not allowed to proceed to this step")
        elif document_edit.state_name == "FINISHED":
            raise BadRequest("Annotation already finished")
        else:
            raise BadRequest("Invalid state")
        document_edit = self.__document_edit_repository.update_state(
            document_edit_id, state.id
        )
        return {
            "id": document_edit.id,
            "schema_id": document_edit.schema_id,
            "document_id": document_edit.document_id,
            "mention_model_id": document_edit.mention_model_id,
            "entity_model_id": document_edit.entity_model_id,
            "relation_model_id": document_edit.relation_model_id,
            "state": {
                "id": state.id,
                "state": state.type,
            },
        }

    def get_document_edits_by_schema(self, schema_id):
        """
        Fetch a list of all document edits by schema id.

        :param schema_id: Schema ID to query
        :return: document_edit_schema_output_dto
        """
        document_edits = self.__document_edit_repository.get_document_edits_by_schema(
            schema_id
        )
        return [
            {
                "document": {
                    "id": document_edit.document_id,
                    "name": document_edit.document_name,
                },
                "id": document_edit.id,
                "state": {
                    "id": document_edit.state_id,
                    "type": document_edit.state_name,
                },
                "user": {
                    "id": document_edit.user_id,
                    "email": document_edit.email,
                    "username": document_edit.username,
                },
            }
            for document_edit in document_edits
        ]

    def get_document_edits_for_schema_training(self, document_edit_ids, schema_id):
        """
        Fetch list of document edits with all required information for model training.
        Returned DocumentEdit dict contains tokens, mentions, relations and entities.

        :param document_edit_ids: DocumentEdit IDs to query.
        :param schema_id: Schema of the documents.
        :return: Dict containing required data for training.
        :raises BadRequest: If document edit does not exist or does not belong to schema.
        """
        # Fetch all document edits of schema
        document_edits = self.__document_edit_repository.get_document_edit_ids_with_document_by_schema(
            schema_id, document_edit_ids
        )

        document_edit_ids = set(document_edit_ids)
        if not len(document_edit_ids) == len(document_edits):
            raise BadRequest("At least one Document Edit does not belong to schema")

        # Create dict mapping document edit ID -> document id, document content
        doc_edit_to_doc_id_map = {}
        doc_edit_to_content_map = {}
        for edit_id, document_id, content in document_edits:
            doc_edit_to_doc_id_map[edit_id] = document_id
            doc_edit_to_content_map[edit_id] = content

        # Create dict mapping document id -> token list
        document_tokens_dict = self.token_service.get_tokens_by_document_ids(
            doc_edit_to_doc_id_map.values()
        )

        # Create dict mapping document edit id -> token list
        document_edit_tokens_dict = {
            document_edit_id: document_tokens_dict[
                doc_edit_to_doc_id_map[document_edit_id]
            ]
            for document_edit_id in document_edit_ids
        }

        # Create dict mapping mention id -> mention
        mention_dict = self.mention_service.get_mentions_by_edit_ids(document_edit_ids)

        document_edit_mention_dict = {
            document_edit_id: [] for document_edit_id in document_edit_ids
        }
        document_edit_entity_dict = {
            document_edit_id: [] for document_edit_id in document_edit_ids
        }
        entity_mention_dict = {
            mention["entity_id"]: [] for mention in mention_dict.values()
        }

        # Create dict mapping document edit id ->  list
        # Create dict mapping entity id -> mention list
        for mention in mention_dict.values():
            document_edit_mention_dict[mention["document_edit_id"]].append(mention)
            if mention["entity_id"] is not None:
                entity_mention_dict[mention["entity_id"]].append(mention)

        # Create dict mapping document edit id -> entity list
        for mention_list in entity_mention_dict.values():
            if len(mention_list) > 0:
                document_edit_entity_dict[mention_list[0]["document_edit_id"]].append(
                    {
                        "id": mention_list[0]["entity_id"],
                        "tag": mention_list[0]["tag"],
                        "mentions": mention_list,
                    }
                )

        # Create dict mapping document edit id -> relation list
        document_edit_relations_dict = (
            self.relation_service.get_document_edit_to_relation_dict(
                document_edit_ids, mention_dict
            )
        )

        # Build response from dict mappings
        return [
            {
                "id": edit_id,
                "content": doc_edit_to_content_map[edit_id],
                "tokens": document_edit_tokens_dict[edit_id],
                "mentions": document_edit_mention_dict[edit_id],
                "entitys": document_edit_entity_dict[edit_id],
                "relations": document_edit_relations_dict[edit_id],
            }
            for edit_id in document_edit_ids
        ]

    def get_f1_score(self, document_edit_id):
        f1_score_request = self.get_document_edit_for_f1_score(document_edit_id)
        return self.f1_score_service.get_f1_score(f1_score_request)

    def get_document_edit_for_f1_score(self, document_edit_id):
        document_edit = self.__document_edit_repository.get_document_edit_by_id(
            document_edit_id
        )
        if document_edit is None:
            raise BadRequest("Document Edit doesnt exist")

        tokens_data = self.token_service.get_tokens_by_document(
            document_edit.document_id
        )
        tokens = tokens_data.get("tokens", [])

        actual_mentions = self.mention_service.get_actual_mentions_by_document_edit(
            document_edit_id
        )
        predicted_mentions = (
            self.mention_service.get_predicted_mentions_by_document_edit(
                document_edit_id
            )
        )

        mentions_data = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )
        mentions_dict = {
            mention["id"]: mention for mention in mentions_data["mentions"]
        }

        actual_relations = (
            self.relation_service.get_actual_relations_by_document_edit_id(
                document_edit_id, mentions_dict
            )
        )

        predicted_relations = (
            self.relation_service.get_predicted_relations_by_document_edit_id(
                document_edit_id, mentions_dict
            )
        )

        actual_document_edit = {
            "document": {
                "id": document_edit.document_id,
                "tokens": tokens,
            },
            "mentions": actual_mentions,
            "relations": actual_relations,
        }

        predicted_document_edit = {
            "document": {
                "id": document_edit.document_id,
                "tokens": tokens,
            },
            "mentions": predicted_mentions,
            "relations": predicted_relations,
        }

        return {"actual": actual_document_edit, "predicted": predicted_document_edit}

    def get_scope_combinations(self, user_id, ref_doc_edit_id, comp_doc_edit_id):
        ref_edit = self.get_document_edit_by_id(ref_doc_edit_id)
        comp_edit = self.get_document_edit_by_id(comp_doc_edit_id)
        if not ref_edit["document"]["id"] == comp_edit["document"]["id"]:
            raise BadRequest("Document edits do not belong to same document")

        tokens = self.token_service.get_tokens_by_document(ref_edit["document"]["id"])[
            "tokens"
        ]

        combos = self.scope_service.get_scope_combinations(
            self.scope_service.get_scope_tree_by_document_edit_id(ref_doc_edit_id),
            self.scope_service.get_scope_tree_by_document_edit_id(comp_doc_edit_id),
            tokens,
        )

        logging.info(len(combos))
        saved_combos = []
        for combo in combos:
            doc_edit = self.create_document_edit(user_id, ref_edit["document"]["id"])
            scope_tree = self.scope_service.save_scope_recommendations(
                doc_edit["id"], combo
            )
            saved_combos.append(scope_tree)
        return saved_combos

    def compute_scope_combinations(
        self,
        user_id,
        document_id,
        interpretations,
        store,
        similarity,
        store_interpretations,
    ):
        all_combos = []
        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        schema = self.schema_service.get_schema_by_document(document_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )
        interpretations = [
            self.document_recommendation_service.map_recommendations_to_scopes(
                i, tokens, schema_scopes
            )
            for i in interpretations
        ]
        interpretation_tree = []
        for i, interpretation in enumerate(interpretations):
            # Avoid same scope ids when building combinations
            for scope in interpretation:
                scope["id"] += 1000 * i
                if scope["parent_scope_id"] is not None:
                    scope["parent_scope_id"] += 1000 * i

            interpretation_tree.append(self.scope_service.rec_to_tree(interpretation))
        for i, ref in enumerate(interpretation_tree):
            for comp in interpretation_tree[i:]:
                if not ref == comp:
                    combos = self.scope_service.get_scope_combinations(
                        copy.deepcopy(ref), copy.deepcopy(comp), tokens
                    )
                    for combo in combos:
                        all_combos.append(combo)

        postprocessed_interpretations = []
        for ref in interpretations:
            postprocessed_interpretations.append(
                self.scope_service.scope_postprocess_service.postprocess_scope_tree(
                    ref,
                    tokens,
                    schema_scopes,
                    schema_scope_constraints,
                    count_violations=True,
                )
            )
        postprocessed_combinations = []
        for combo in all_combos:
            postprocessed_combinations.append(
                self.scope_service.scope_postprocess_service.postprocess_scope_tree(
                    combo,
                    tokens,
                    schema_scopes,
                    schema_scope_constraints,
                    count_violations=False,
                )
            )

        logging.info(f"Combinations: {len(all_combos)}")
        doc_edit_ids = []

        unique_combos = []
        for i, ref_combo in enumerate(postprocessed_combinations):
            unique = True
            for comp_combo in postprocessed_combinations[i:]:
                if not ref_combo == comp_combo:
                    sim = self.scope_service.scope_tree_similarity_obj(
                        self.scope_service.rec_to_tree(ref_combo),
                        self.scope_service.rec_to_tree(comp_combo),
                        tokens,
                        schema_scopes,
                    )
                    if sim["total_similarity"] == 1:
                        unique = False
                        break
            if unique:
                unique_combos.append(ref_combo)

        logging.info(f"Unique Combinations: {len(unique_combos)}")

        if store_interpretations:
            for interpretation in postprocessed_interpretations:
                doc_edit = self.create_document_edit(user_id, document_id)
                self.scope_service.save_scope_recommendations(
                    doc_edit["id"], interpretation
                )
                doc_edit_ids.append(doc_edit["id"])

        if store:
            for combo in unique_combos:
                doc_edit = self.create_document_edit(user_id, document_id)
                self.scope_service.save_scope_recommendations(doc_edit["id"], combo)
                doc_edit_ids.append(doc_edit["id"])

        if similarity:
            for interpretation in postprocessed_interpretations:
                for combo in unique_combos:
                    sim = self.scope_service.scope_tree_similarity_obj(
                        self.scope_service.rec_to_tree(interpretation),
                        self.scope_service.rec_to_tree(combo),
                        tokens,
                        schema_scopes,
                    )
                    logging.info(sim["total_similarity"])

        json_object = {
            "interpretations": [
                self.scope_service.scopes_to_output(i)
                for i in postprocessed_interpretations
            ],
            "combinations": [
                self.scope_service.scopes_to_output(c) for c in unique_combos
            ],
        }
        base_dir = os.path.abspath(os.path.dirname(__file__))
        filename = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(base_dir, f"/logs/combinations/{filename}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_object, f)

        logging.info(doc_edit_ids)


document_edit_service = DocumentEditService(
    DocumentEditRepository(),
    document_recommendation_service,
    token_service,
    mention_service,
    relation_service,
    schema_service,
    entity_service,
    f1_score_service,
    scope_service,
    schema_scope_service,
)
