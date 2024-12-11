from app.repositories.entity_repository import EntityRepository
from werkzeug.exceptions import BadRequest, NotFound


class EntityService:
    def __init__(self, entity_repository):
        self.__entity_repository = entity_repository

    def get_entities_by_document_edit(self, document_edit_id):
        if not isinstance(document_edit_id, int) or document_edit_id <= 0:
            raise BadRequest("Invalid document edit ID. It must be a positive integer.")

        entities = self.__entity_repository.get_entities_by_document_edit(
            document_edit_id
        )
        if not entities:
            raise NotFound("No entities found for the given document edit.")

        entity_list = [
            {
                "id": entity.id,
                "isShownRecommendation": entity.isShownRecommendation,
                "document_edit_id": entity.document_edit_id,
                "document_recommendation_id": entity.document_recommendation_id,
            }
            for entity in entities
        ]
        return {"entities": entity_list}


entity_service = EntityService(EntityRepository())
