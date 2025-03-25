from app.models.db_models import DocumentRecommendation
from app.repositories.base_repository import BaseRepository


class DocumentRecommendationRepository(BaseRepository):

    def create_document_recommendation(self, document_id, document_edit_id=None):
        document_recommendation = DocumentRecommendation(
            document_id=document_id,
            document_edit_id=document_edit_id,
            state_id=1,
            documentEditHash="",
        )
        return super().store_object(document_recommendation)

    def get_document_recommendation_by_document_edit(self, document_edit_id):
        return (
            self.get_session()
            .query(DocumentRecommendation)
            .filter(DocumentRecommendation.document_edit_id == document_edit_id)
            .first()
        )
