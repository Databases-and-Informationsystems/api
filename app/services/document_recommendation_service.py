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



    def accept_recommendation(self, recommendation_id):
        recommendation = self.__document_recommendation_repository.find_by_id(recommendation_id)
        if not recommendation:
            raise ValueError("Recommendation not found.")

        document_edit = self.__document_edit_repository.create_from_recommendation(recommendation)
        recommendation.is_shown = False
        self.__document_recommendation_repository.update(recommendation)

        return {"status": "accepted", "document_edit_id": document_edit.id}

    def reject_recommendation(self, recommendation_id):
        recommendation = self.__document_recommendation_repository.find_by_id(recommendation_id)
        if not recommendation:
            raise ValueError("Recommendation not found.")

        recommendation.is_shown = False
        self.__document_recommendation_repository.update(recommendation)

        return {"status": "rejected"}
    
document_recommendation_service = DocumentRecommendationService(
    DocumentRecommendationRepository(), mention_service
)
