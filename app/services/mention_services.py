from werkzeug.exceptions import BadRequest, NotFound, Conflict, Unauthorized

from app.repositories.mention_repository import MentionRepository
from app.services.schema_service import SchemaService, schema_service
from app.services.token_service import TokenService, token_service
from app.services.user_service import UserService, user_service

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
    user_service: UserService
    relation_mention_service: RelationMentionService
    entity_mention_service: EntityMentionService
    token_service: TokenService
    schema_service: SchemaService

    def __init__(
        self,
        mention_repository,
        token_mention_service,
        user_service,
        relation_mention_service,
        entity_mention_service,
        token_service,
        schema_service,
    ):
        self.__mention_repository = mention_repository
        self.token_mention_service = token_mention_service
        self.user_service = user_service
        self.relation_mention_service = relation_mention_service
        self.entity_mention_service = entity_mention_service
        self.token_service = token_service
        self.schema_service = schema_service

    def get_mentions_by_document_edit(self, document_edit_id):
        if not isinstance(document_edit_id, int) or document_edit_id <= 0:
            raise BadRequest("Invalid document edit ID. It must be a positive integer.")

        user_id = user_service.get_user_by_document_edit_id(document_edit_id)
        current_user_id = self.user_service.get_logged_in_user_id()

        if current_user_id != user_id:
            raise Unauthorized("You are not authorized to perform this action.")

        results = self.__mention_repository.get_mentions_with_tokens_by_document_edit(
            document_edit_id
        )

        mentions_dict = {}
        for row in results:
            if row.mention_id not in mentions_dict:
                mentions_dict[row.mention_id] = {
                    "id": row.mention_id,
                    "tag": row.tag,
                    "isShownRecommendation": row.isShownRecommendation,
                    "document_edit_id": row.document_edit_id,
                    "document_recommendation_id": row.document_recommendation_id,
                    "entity_id": row.entity_id,
                    "tokens": [],
                    "schema_mention": {
                        "id": row.schema_mention_id,
                        "tag": row.tag,
                        "description": row.description,
                        "color": row.color,
                        "entityPossible": row.entityPossible,
                    },
                }

            if row.token_id is not None:
                mentions_dict[row.mention_id]["tokens"].append(
                    {
                        "id": row.token_id,
                        "text": row.text,
                        "document_index": row.document_index,
                        "sentence_index": row.sentence_index,
                        "pos_tag": row.pos_tag,
                    }
                )
        return {"mentions": list(mentions_dict.values())}

    def create_mentions(self, data):
        # check if user is allowed to access this document edit
        logged_in_user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(
            logged_in_user_id, data["document_edit_id"]
        )

        # Check that tokens belong to this document
        self.token_service.check_tokens_in_document_edit(
            data["token_ids"], data["document_edit_id"]
        )

        # check duplicates
        duplicate_token_mention = self.check_token_in_mention(
            data["document_edit_id"], data["token_ids"]
        )
        if len(duplicate_token_mention) > 0:
            raise Conflict("Token mention already exists.")

        # Check Tag is allowed
        schema = self.schema_service.get_schema_by_document_edit(
            data["document_edit_id"]
        )
        schema_mention = self.schema_service.get_schema_mention_by_id(
            data["schema_mention_id"]
        )
        if schema_mention.schema_id != schema.id:
            raise BadRequest("Mention Tag not allowed")

        # save mention
        mention = self.__mention_repository.create_mention(
            document_edit_id=data["document_edit_id"],
            schema_mention_id=data["schema_mention_id"],
        )

        # save token mention
        for token_id in data["token_ids"]:
            self.token_mention_service.create_token_mention(token_id, mention.id)

        mention.tokens = data["token_ids"]
        mention.tag = schema_mention.tag
        mention.schema_mention = schema_mention
        return mention

    def add_to_entity(self, entity_id: int, mention_id: int):
        self.__mention_repository.add_to_entity(entity_id, mention_id)

    def copy_mention_recommendations_to_document_edit(
        self,
        document_recommendation_id_source,
        document_edit_id_target,
        document_recommendation_id_target,
    ):
        if document_recommendation_id_source is None:
            return

        mentions = self.__mention_repository.get_mentions_by_document_recommendation(
            document_recommendation_id_source
        )
        if mentions:
            for mention in mentions:
                self.__mention_repository.create_mention(
                    mention.schema_mention_id,
                    document_edit_id=document_edit_id_target,
                    document_recommendation_id=document_recommendation_id_target,
                    is_shown_recommendation=True,
                )

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

        user_id = user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, mention.document_edit_id
        )

        related_relations = self.relation_mention_service.get_relations_by_mention(
            mention_id
        )
        for relation in related_relations:
            self.relation_mention_service.delete_relation_by_id(relation.id)

        self.token_mention_service.delete_token_mentions_by_mention_id(mention_id)

        deleted = self.__mention_repository.delete_mention_by_id(mention_id)

        self.delete_entity_if_empty(mention.entity_id)

        if not deleted:
            raise NotFound("Mention not found during deletion.")

        return {"message": "OK"}

    def delete_entity_if_empty(self, entity_id):
        if entity_id is not None:
            mentions_with_entity = self.__mention_repository.get_mentions_by_entity_id(
                entity_id
            )

            if len(mentions_with_entity) == 0:
                self.entity_mention_service.delete_entity(entity_id)

    def update_mention(self, mention_id, schema_mention_id, token_ids, entity_id):
        # Check that mention exists
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        if not mention:
            raise NotFound("Mention not found.")

        if mention.document_recommendation_id:
            raise BadRequest("You cannot update a recommendation")

        schema = self.schema_service.get_schema_by_document_edit(
            mention.document_edit_id
        )

        # Check that user owns this document edit
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, mention.document_edit_id
        )

        # Check for valid tag
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
            for duplicate_token in duplicate_tokens:
                if duplicate_token.mention_id != mention_id:
                    raise Conflict("Token already part of mention")

            # Update token mentions
            self.token_mention_service.delete_token_mentions_by_mention_id(mention_id)
            for token_id in token_ids:
                self.token_mention_service.create_token_mention(token_id, mention_id)

        if entity_id is not None or mention.entity_id is not None:
            if not schema_mention.entityPossible:
                raise BadRequest("Entity not allowed for this mention")

        # Delete entity if it is empty after update, id = 0: clear entity_id of mention
        if entity_id is not None:
            if entity_id != 0:
                self.entity_mention_service.check_entity_in_document_edit(
                    entity_id, mention.document_edit_id
                )

        updated_mention = self.__mention_repository.update_mention(
            mention_id, schema_mention_id, entity_id
        )

        if mention.entity_id and entity_id != mention.entity_id:
            self.delete_entity_if_empty(mention.entity_id)

        token_mentions = self.token_mention_service.get_token_mentions_by_mention_id(
            mention_id
        )
        return {
            "id": updated_mention.id,
            "tag": schema_mention.tag,
            "is_shown_recommendation": updated_mention.isShownRecommendation,
            "document_edit_id": updated_mention.document_edit_id,
            "document_recommendation_id": updated_mention.document_recommendation_id,
            "entity_id": updated_mention.entity_id,
            "tokens": [token_mention.token_id for token_mention in token_mentions],
            "schema_mention": {
                "id": schema_mention.id,
                "tag": schema_mention.tag,
                "description": schema_mention.description,
                "color": schema_mention.color,
                "entityPossible": schema_mention.entityPossible,
            },
        }

    def check_token_in_mention(self, document_edit_id, token_ids):
        # check duplicates
        mentions = self.__mention_repository.get_mentions_with_tokens_by_document_edit(
            document_edit_id
        )
        if len(mentions) > 0:

            mention_ids = []
            for mention in mentions:
                mention_ids.append(mention.mention_id)

            duplicate_token_mention = token_mention_service.get_token_mention(
                token_ids, mention_ids
            )
            return duplicate_token_mention
        return []

    def accept_mention(self, mention_id):
        """
        Accept a mention by copying it to the document edit and setting isShownRecommendation to False.
        """
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, mention.document_edit_id
        )
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
        )

        # Add tokens to mention
        token_mentions = self.token_mention_service.get_token_mentions_by_mention_id(
            mention_id
        )
        tokens = []
        for token_mention in token_mentions:
            self.token_mention_service.create_token_mention(
                token_mention.token_id, new_mention.id
            )
            tokens.append(token_mention.token_id)

        # Update mention recommendation
        self.__mention_repository.update_is_shown_recommendation(mention_id, False)
        schema_mention = self.schema_service.get_schema_mention_by_id(
            mention.schema_mention_id
        )
        new_mention.tokens = tokens
        new_mention.schema_mention = schema_mention
        new_mention.tag = schema_mention.tag
        return new_mention

    def reject_mention(self, mention_id):
        """
        Reject a mention by setting isShownRecommendation to False.
        """
        mention = self.__mention_repository.get_mention_by_id(mention_id)
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_edit_accessible(
            user_id, mention.document_edit_id
        )
        if not mention or mention.document_recommendation_id is None:
            raise BadRequest("Invalid mention")
        if not mention.isShownRecommendation:
            raise BadRequest("Mention recommendation already processed.")

        # Update mention recommendation
        self.__mention_repository.update_is_shown_recommendation(mention_id, False)
        return {"message": "Mention successfully rejected."}

    def get_mention_by_id(self, mention_id):
        return self.__mention_repository.get_mention_by_id(mention_id)

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


mention_service = MentionService(
    MentionRepository(),
    token_mention_service,
    user_service,
    relation_mention_service,
    entity_mention_service,
    token_service,
    schema_service,
)
