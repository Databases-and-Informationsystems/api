from app.repositories.document_recommendation_repository import (
    DocumentRecommendationRepository,
)
from app.services.mention_services import MentionService, mention_service


class DocumentRecommendationService:
    __document_recommendation_repository: DocumentRecommendationRepository
    mention_service: MentionService

    def __init__(self, document_recommendation_repository, mention_service):
        self.__document_recommendation_repository = document_recommendation_repository
        self.mention_service = mention_service

    def create_document_recommendation(self, document_id=None, document_edit_id=None):
        return self.__document_recommendation_repository.create_document_recommendation(
            document_id, document_edit_id
        )

    def copy_document_recommendations(
        self,
        document_recommendation_id_source,
        document_edit_id_target,
        document_recommendation_id_target,
    ):
        self.mention_service.copy_mention_recommendations_to_document_edit(
            document_recommendation_id_source,
            document_edit_id_target,
            document_recommendation_id_target,
        )


document_recommendation_service = DocumentRecommendationService(
    DocumentRecommendationRepository(), mention_service
)
