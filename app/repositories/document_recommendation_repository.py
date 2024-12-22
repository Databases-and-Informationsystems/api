from app.models import DocumentRecommendation
from app.db import db
from app.repositories.base_repository import BaseRepository


class DocumentRecommendationRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def create_document_recommendation(self, document_id, document_edit_id=None):
        document_recommendation = DocumentRecommendation(
            document_id=document_id,
            document_edit_id=document_edit_id,
            state_id=1,
            documentEditHash="",
        )
        super().store_object(document_recommendation)
        return document_recommendation
