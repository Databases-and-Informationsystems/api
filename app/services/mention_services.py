from typing import List

from werkzeug.exceptions import BadRequest, NotFound, Conflict

from app.models.buisness_models import BMention
from app.repositories.mention_repository import MentionRepository
from app.services.schema_service import SchemaService, schema_service
from app.services.token_service import TokenService, token_service

from app.services.relation_mention_service import (
    RelationMentionService,
    relation_mention_service,
)
from app.services.entity_mention_service import (
    EntityMentionService,
    entity_mention_service,
)

from app.services.token_mention_service import (
    token_mention_service,
    TokenMentionService,
)


class MentionService:
    __mention_repository: MentionRepository
    token_mention_service: TokenMentionService
    relation_mention_service: RelationMentionService
    entity_mention_service: EntityMentionService
    token_service: TokenService
    schema_service: SchemaService

    def __init__(
        self,
        mention_repository,
        token_mention_service,
        relation_mention_service,
        entity_mention_service,
        token_service,
        schema_service,
    ):
        self.__mention_repository = mention_repository
        self.token_mention_service = token_mention_service
        self.relation_mention_service = relation_mention_service
        self.entity_mention_service = entity_mention_service
        self.token_service = token_service
        self.schema_service = schema_service

    def get_mentions_by_document_edit(self, document_edit_id: int) -> List[BMention]:
        if not isinstance(document_edit_id, int) or document_edit_id <= 0:
            raise BadRequest("Invalid document edit ID. It must be a positive integer.")

        return self.__mention_repository.get_mentions_by_edit_ids([document_edit_id])

    def get_mention_dto_by_id(self, mention_id):
        """
        Fetches mention with associated tokens by mention ID and maps to output dto.

        :param mention_id: Mention ID to query.
        :return: mention_output_dto
        """
        mention = self.__mention_repository.get_mention_with_schema_by_id(mention_id)
        tokens = self.token_service.get_tokens_by_mention(mention_id)
        return {
            "id": mention.mention_id,
            "tag": mention.tag,
            "is_shown_recommendation": mention.isShownRecommendation,
            "document_edit_id": mention.document_edit_id,
            "document_recommendation_id": mention.document_recommendation_id,
            "entity_id": mention.entity_id,
            "tokens": tokens["tokens"],
            "schema_mention": {
                "id": mention.schema_mention_id,
                "tag": mention.tag,
                "description": mention.description,
                "color": mention.color,
                "entityPossible": mention.entityPossible,
            },
        }

    def create_mention(
        self, document_edit_id, schema_mention_id, token_ids
    ) -> BMention:

        # Check that tokens belong to this document
        self.token_service.check_tokens_in_document_edit(token_ids, document_edit_id)

        # check duplicates
        duplicate_token_mention = self.check_token_in_mention(
            document_edit_id, token_ids
        )
        if len(duplicate_token_mention) > 0:
            raise Conflict("Token mention already exists.")

        # Check Tag is allowed
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_mention = self.schema_service.get_schema_mention_by_id(schema_mention_id)
        if schema_mention.schema_id != schema.id:
            raise BadRequest("Mention Tag not allowed")

        # save mention
        mention = self.__mention_repository.create_mention(
            document_edit_id=document_edit_id,
            schema_mention_id=schema_mention_id,
        )

        # save token mention
        for token_id in token_ids:
            self.token_mention_service.create_token_mention(token_id, mention.id)

        return self.get_mention_by_id(mention.id)

    def add_to_entity(self, entity_id: int, mention_id: int):
        """
        Add a mention to an existing entity.
        Does not check for valid inputs.

        :param entity_id: Entity ID to add mention to.
        :param mention_id: Mention ID to add to entity.
        :return: Updated Mention
        """
        self.__mention_repository.add_to_entity(entity_id, mention_id)

    def delete_mention(self, mention_id):
        if not isinstance(mention_id, int) or mention_id <= 0:
            raise BadRequest("Invalid mention ID. It must be a positive integer.")

        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention:
            raise NotFound("Mention not found.")

        if mention.document_edit_id is None:
            raise BadRequest(
                "Cannot delete a mention without a valid document_edit_id."
            )

        related_relations = self.relation_mention_service.get_relations_by_mention(
            mention_id
        )
        for relation in related_relations:
            self.relation_mention_service.delete_relation_by_id(relation.id)

        self.token_mention_service.delete_token_mentions_by_mention_id(mention_id)

        deleted = self.__mention_repository.delete_mention_by_id(mention_id)

        self.__delete_entity_if_empty(mention.entity_id)

        if not deleted:
            raise NotFound("Mention not found during deletion.")

        return {"message": "OK"}

    def __delete_entity_if_empty(self, entity_id):
        """
        Deletes an entity if it contains no mentions.

        :param entity_id: Entity ID to delete.
        """
        if entity_id is not None:
            mentions_with_entity = self.__mention_repository.get_mentions_by_entity_id(
                entity_id
            )

            if len(mentions_with_entity) == 0:
                self.entity_mention_service.delete_entity(entity_id)

    def update_mention(self, mention_id, schema_mention_id, token_ids, entity_id):
        """
        Updates a mention.
        To remove entity ID from the mention, pass entity ID = 0.
        If an entity is empty afterward, it will be deleted.

        :param mention_id: Mention ID to update.
        :param schema_mention_id: Updated schema mention ID.
        :param token_ids: Updated token IDs.
        :param entity_id: Updated entity ID.
        :return: mention_output_dto
        :raises NotFound: If mention does not exist.
        :raises Conflict: If tokens already part of another mention.
        :raises BadRequest: If schema mention not allowed, entity not allowed or mention is a recommendation.
        :raises Forbidden: If entity or tokens do not belong to the document edit.
        """
        # Check that mention exists
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention:
            raise NotFound("Mention not found.")

        if mention.document_recommendation_id:
            raise BadRequest("You cannot update a recommendation")

        # Fetch schema
        schema = self.schema_service.get_schema_by_document_edit(
            mention.document_edit_id
        )

        # Fetch schema mention
        if schema_mention_id is not None:
            schema_mention = self.schema_service.get_schema_mention_by_id(
                schema_mention_id
            )
        else:
            schema_mention = self.schema_service.get_schema_mention_by_id(
                mention.schema_mention_id
            )
        if schema_mention.schema_id != schema.id:
            raise BadRequest("Mention Tag not allowed")

        if token_ids:
            # Check that tokens belong to this document
            self.token_service.check_tokens_in_document_edit(
                token_ids, mention.document_edit_id
            )
            # Check that tokens are not used in other mention
            duplicate_tokens = self.check_token_in_mention(
                mention.document_edit_id, token_ids
            )
            # Do not raise exception if tokens are used by mention to update.
            for duplicate_token in duplicate_tokens:
                if duplicate_token.mention_id != mention_id:
                    raise Conflict("Token already part of mention")

            # Update token mentions
            self.token_mention_service.delete_token_mentions_by_mention_id(mention_id)
            for token_id in token_ids:
                self.token_mention_service.create_token_mention(token_id, mention_id)

        # Raise exception if entity is specified but forbidden by schema
        if entity_id is not None or mention.entity_id is not None:
            if not schema_mention.entityPossible:
                raise BadRequest("Entity not allowed for this mention")

        # Check if entity id belongs to document edit
        if entity_id is not None:
            if entity_id != 0:
                self.entity_mention_service.check_entity_in_document_edit(
                    entity_id, mention.document_edit_id
                )

        # Update mention, entity id = 0:  clear entity_id of mention
        updated_mention = self.__mention_repository.update_mention(
            mention_id, schema_mention_id, entity_id
        )

        # Delete entity if it is empty
        if mention.entity_id and entity_id != mention.entity_id:
            self.__delete_entity_if_empty(mention.entity_id)

        return self.get_mention_dto_by_id(updated_mention.id)

    def check_token_in_mention(self, document_edit_id, token_ids):
        """
        Check if tokens are already part of mentions of a document edit.

        :param document_edit_id: DocumentEdit ID to check tokens.
        :param token_ids: Token IDs to check.
        :return: List of duplicate tokens, empty list if no duplicates found.
        """
        # Fetch mentions of document edit
        mentions = self.__mention_repository.get_mentions_with_tokens_by_document_edit(
            document_edit_id
        )
        if len(mentions) > 0:

            mention_ids = []
            for mention in mentions:
                mention_ids.append(mention.mention_id)

            # Find duplicate tokens
            duplicate_token_mention = self.token_mention_service.get_token_mention(
                token_ids, mention_ids
            )
            return duplicate_token_mention
        return []

    def accept_mention(self, mention_id):
        """
        Accept a mention by copying it to the document edit and setting isShownRecommendation to False.
        """
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention or mention.document_recommendation_id is None:
            raise BadRequest("Invalid mention")
        if not mention.isShownRecommendation:
            raise BadRequest("Mention recommendation already processed.")

        # Create new mention
        new_mention = self.__mention_repository.create_mention(
            schema_mention_id=mention.schema_mention_id,
            document_edit_id=mention.document_edit_id,
            document_recommendation_id=None,
            is_shown_recommendation=False,
            entity_id=mention.entity_id,
        )

        # Add tokens to mention
        token_mentions = self.token_mention_service.get_token_mentions_by_mention_id(
            mention_id
        )
        for token_mention in token_mentions:
            self.token_mention_service.create_token_mention(
                token_mention.token_id, new_mention.id
            )

        # Update mention recommendation
        self.__mention_repository.update_is_shown_recommendation(mention_id, False)
        return self.get_mention_dto_by_id(new_mention.id)

    def reject_mention(self, mention_id):
        """
        Reject a mention by setting isShownRecommendation to False.
        """
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention or mention.document_recommendation_id is None:
            raise BadRequest("Invalid mention")
        if not mention.isShownRecommendation:
            raise BadRequest("Mention recommendation already processed.")

        # Update mention recommendation
        self.__mention_repository.update_is_shown_recommendation(mention_id, False)
        return {"message": "Mention successfully rejected."}

    def get_mention_by_id(self, mention_id) -> BMention:
        """
        Returns mention database entry for given mention ID.
        :param mention_id: MentionID to fetch.
        :return: Mention database entry.
        :raises NotFound: If mention does not exist
        """
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention:
            raise NotFound("Mention does not exist")
        return mention

    def create_recommended_mention(
        self, document_edit_id, document_recommendation_id, mention_recommendations
    ):
        for mention_recommendation in mention_recommendations:
            mention = self.__mention_repository.create_mention(
                mention_recommendation["mention_schema_id"],
                document_edit_id,
                document_recommendation_id,
                is_shown_recommendation=True,
            )
            for token_id in mention_recommendation["token_ids"]:
                self.token_mention_service.create_token_mention(token_id, mention.id)

    def verify_mention_in_document_edit_not_recommendation(
        self, mention_id, document_edit_id
    ):
        """
        Check that mention is in document edit and is not a recommendation.

        :param mention_id: MentionID to check.
        :param document_edit_id: DocumentEdit ID to check.
        :return: Mention database entry
        :raises NotFound: If mention does not exist
        :raises BadRequest: If mention does not belong to document edit or is a recommendation.
        """
        mention = self.get_mention_by_id(mention_id)

        # check if mention belongs to same edit
        if mention.document_edit_id != document_edit_id:
            raise BadRequest("Mentions do not belong to this document.")

        if mention.document_recommendation_id:
            raise BadRequest("You cannot use a recommendation inside the relation")
        return mention

    def check_mentions_not_equal(self, mention_head_id, mention_tail_id):
        """
        Check if two mentions are equal.

        :param mention_head_id: MentionID to compare.
        :param mention_tail_id: MentionID to compare.
        :raises BadRequest: If mentions are equal
        """
        if mention_head_id == mention_tail_id:
            raise BadRequest("Mentions are equal")

    def get_recommendations_by_document_edit(self, document_edit_id):
        """
        Fetches all unreviewed mention recommendations for a document edit

        :param document_edit_id: Document Edit ID to query
        :return: List of mention database entries
        """
        return self.__mention_repository.get_recommendations_by_document_edit(
            document_edit_id
        )

    def get_mentions_by_edit_ids(self, document_edit_ids):
        """
        Fetch mentions by list of document edit IDs

        :param document_edit_ids: List of document edit IDs
        :return: Mention dict containing mentions by mention ID
        """
        mentions = self.__mention_repository.get_mentions_by_edit_ids(document_edit_ids)
        mention_dict = {}
        for mention in mentions:
            if mention.id not in mention_dict:
                mention_dict[mention.id] = {
                    "tag": mention.tag,
                    "id": mention.id,
                    "document_edit_id": mention.document_edit_id,
                    "entity_id": mention.entity_id,
                    "tokens": [],
                }
            mention_dict[mention.id]["tokens"].append(
                {
                    "id": mention.token_id,
                    "text": mention.text,
                    "document_index": mention.document_index,
                    "sentence_index": mention.sentence_index,
                    "pos_tag": mention.pos_tag,
                }
            )

        return mention_dict

    def get_actual_mentions_by_document_edit(self, document_edit_id):
        actual_mentions = (
            self.__mention_repository.get_actual_mentions_with_tokens_by_document_edit(
                document_edit_id
            )
        )
        return self.__map_mentions_to_f1_score_dto(actual_mentions)

    def get_predicted_mentions_by_document_edit(self, document_edit_id):
        predicted_mentions = self.__mention_repository.get_predicted_mentions_with_tokens_by_document_edit(
            document_edit_id
        )
        return self.__map_mentions_to_f1_score_dto(predicted_mentions)

    def __map_mentions_to_f1_score_dto(self, mentions):
        # Create a dictionary to group tokens by mention_id
        mentions_map = {}

        for mention in mentions:
            mention_id = mention.mention_id

            # If the mention is not already in the map, add it
            if mention_id not in mentions_map:
                mentions_map[mention_id] = {
                    "tag": mention.tag,
                    "tokens": [],
                    **(
                        {"entity": {"id": mention.entity_id}}
                        if mention.entity_id
                        else {"entity": {"id": 0}}
                    ),
                }

            # Add token data to the mention's tokens list
            if mention.token_id is not None:  # Ensure token data exists
                mentions_map[mention_id]["tokens"].append(
                    {
                        "id": mention.token_id,
                        "text": mention.text,
                        "document_index": mention.document_index,
                        "sentence_index": mention.sentence_index,
                        "pos_tag": mention.pos_tag,
                    }
                )

        # Convert the dictionary to a list of mentions
        mentions_list = list(mentions_map.values())

        return mentions_list


mention_service = MentionService(
    MentionRepository(),
    token_mention_service,
    relation_mention_service,
    entity_mention_service,
    token_service,
    schema_service,
)
