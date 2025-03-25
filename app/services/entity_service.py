import typing

from app.models.buisness_models import BEntity
from app.models.db_models import Entity
from app.repositories.entity_repository import EntityRepository
from werkzeug.exceptions import BadRequest, NotFound

from app.services.entity_mention_service import (
    entity_mention_service,
    EntityMentionService,
)
from app.services.mention_services import MentionService, mention_service
from app.services.schema_service import schema_service, SchemaService


class EntityService:
    __entity_repository: EntityRepository
    schema_service: SchemaService
    entity_mention_service: EntityMentionService
    mention_service: MentionService

    def __init__(
        self,
        entity_repository,
        schema_service,
        entity_mention_service,
        mention_service,
    ):
        self.__entity_repository = entity_repository
        self.schema_service = schema_service
        self.entity_mention_service = entity_mention_service
        self.mention_service = mention_service

    def get_entities_by_document_edit(self, document_edit_id) -> typing.List[BEntity]:
        if not isinstance(document_edit_id, int) or document_edit_id <= 0:
            raise BadRequest("Invalid document edit ID. It must be a positive integer.")

        entities = self.__entity_repository.get_entities_by_document_edit(
            document_edit_id
        )

        mentions = self.mention_service.get_mentions_by_document_edit(document_edit_id)

        for entity in entities:
            entity.mentions = [m for m in mentions if m.entity_id == entity.id]

        return entities

    def create_in_edit(self, document_edit_id: int) -> Entity:
        """
        Create a new empty entity for given documentEdit.

        :param document_edit_id: DocumentEdit ID to create entity for.
        :return: Newly created entity.
        """
        return self.__entity_repository.create_in_edit(document_edit_id)

    def delete_entity(self, entity_id):
        entity = self.__entity_repository.get_entity_by_id(entity_id)
        if entity is None:
            raise NotFound("No entity found for the given ID.")
        return self.entity_mention_service.delete_entity(entity_id)

    def create_entity(self, document_edit_id, mention_ids):
        """
        Create an empty entity for given documentEdit.
        Adds specified mentions to the entity.

        :param document_edit_id: DocumentEdit ID to create entity for.
        :param mention_ids: Mention IDs to add into the entity.
        :return: entity_output_dto
        :raises BadRequest: If mention IDs are invalid or mentions must not be part of an entity.
        """
        # Fetch all mentions of document
        mentions_of_edit = self.mention_service.get_mentions_by_document_edit(
            document_edit_id
        )

        # Filter mentions of entity
        mentions_of_entity = [
            mention
            for mention in mentions_of_edit["mentions"]
            if mention["id"] in mention_ids
        ]

        # Check if a mention does not exist
        if len(mentions_of_entity) != len(mention_ids):
            raise BadRequest("Invalid mention ids.")

        for mention in mentions_of_entity:

            # Check that entity is allowed for mentions
            if not mention["schema_mention"]["entityPossible"]:
                raise BadRequest("Entity not allowed for this mention")

        # save entity
        entity = self.__entity_repository.create_entity(document_edit_id)

        # add entity id to mention or replace previous one
        for mention in mentions_of_entity:
            self.mention_service.add_to_entity(entity.id, mention["id"])
            mention["entity_id"] = entity.id

        response = {
            "id": entity.id,
            "isShownRecommendation": entity.isShownRecommendation,
            "document_edit_id": entity.document_edit_id,
            "document_recommendation_id": entity.document_recommendation_id,
            "mentions": mentions_of_entity,
        }
        return response

    def create_entity_for_mentions(self, document_edit_id):
        """
        Creates a new entity for each mention that is not part of an entity, but may be part of one.

        :param document_edit_id: DocumentEdit ID to create entity for.
        :return: mention_output_list_dto
        """
        mentions = self.mention_service.get_mentions_by_document_edit(document_edit_id)
        mentions_without_entity = []
        for mention in mentions["mentions"]:
            if (
                mention["entity_id"] is None
                and mention["schema_mention"]["entityPossible"] is True
            ):
                mentions_without_entity.append(mention)

        for mention in mentions_without_entity:
            entity = self.__entity_repository.create_entity(document_edit_id)
            self.mention_service.add_to_entity(entity.id, mention["id"])
            mention["entity_id"] = entity.id
        return mentions_without_entity

    def save_entity_in_edit(
        self, document_edit_id, mentions, document_recommendation_id
    ):
        entity = self.__entity_repository.create_entity(
            document_edit_id,
            document_recommendation_id=document_recommendation_id,
            is_shown_recommendation=True,
        )
        for mention in mentions:
            self.mention_service.add_to_entity(entity.id, mention["id"])


entity_service = EntityService(
    EntityRepository(),
    schema_service,
    entity_mention_service,
    mention_service,
)
