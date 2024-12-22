from werkzeug.exceptions import BadRequest

from app.repositories.document_edit_repository import DocumentEditRepository
from app.services.document_recommendation_service import (
    DocumentRecommendationService,
    document_recommendation_service,
)
from app.services.document_service import DocumentService, document_service
from app.services.user_service import UserService, user_service


class DocumentEditService:
    __document_edit_repository: DocumentEditRepository
    document_service: DocumentService
    user_service: UserService
    document_recommendation_service: DocumentRecommendationService

    def __init__(
        self,
        document_edit_repository: DocumentEditRepository,
        document_service: DocumentService,
        user_service: UserService,
        document_recommendation_service: DocumentRecommendationService,
    ):
        self.__document_edit_repository = document_edit_repository
        self.document_service = document_service
        self.user_service = user_service
        self.document_recommendation_service = document_recommendation_service

    def create_document_edit(self, document_id):
        user_id = 1  # self.user_service.get_logged_in_user_id()

        # Check if document edit already exists
        doc_edit = self.get_document_edit_by_document(document_id, user_id)
        if doc_edit is not None:
            raise BadRequest("Document Edit already exists")
        document = self.document_service.get_document_by_id(document_id)
        if document is None:
            raise BadRequest("Document does not exist")
        self.user_service.check_user_in_team(user_id, document.team_id)

        # Create document edit
        document_edit = self.__document_edit_repository.create_document_edit(
            document_id, user_id, document.schema_id
        )

        # Create document recommendation for document edit
        document_recommendation = (
            self.document_recommendation_service.create_document_recommendation(
                document_edit_id=document_edit.id, document_id=document_id
            )
        )

        # Copy mention recommendations from document to new document edit
        self.document_recommendation_service.copy_document_recommendations(
            document.document_recommendation_id,
            document_edit.id,
            document_recommendation.id,
        )
        return {
            "id": document_edit.id,
            "schema_id": document_edit.schema_id,
            "document_id": document_edit.document_id,
        }

    def get_document_edit_by_document(self, document_id, user_id):
        return self.__document_edit_repository.get_document_edit_by_document(
            document_id, user_id
        )


document_edit_service = DocumentEditService(
    DocumentEditRepository(),
    document_service,
    user_service,
    document_recommendation_service,
)
