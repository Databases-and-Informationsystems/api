from werkzeug.exceptions import NotFound

from app.repositories.document_repository import DocumentRepository
from app.services.user_service import UserService, user_service
from app.services.token_service import TokenService, token_service


class DocumentService:
    __document_repository: DocumentRepository
    user_service: UserService
    token_service: TokenService

    def __init__(self, document_repository, user_service, token_service):
        self.__document_repository = document_repository
        self.user_service = user_service
        self.token_service = token_service

    def get_documents_by_project(self, project_id):
        documents = self.get_documents_by_user()
        return [
            document for document in documents if document["project_id"] == project_id
        ]

    def get_documents_by_user(self):
        user_id = 1  # self.user_service.get_logged_in_user_id()
        documents = self.__document_repository.get_documents_by_user(user_id)
        if not documents:
            raise NotFound("No documents found")
        document_list = [
            {
                "content": doc.content,
                "id": doc.id,
                "name": doc.name,
                "project_id": doc.project_id,
                "project_name": doc.project_name,
                "schema_id": doc.schema_id,
                "team_name": doc.team_name,
                "team_id": doc.team_id,
                "document_edit_id": doc.document_edit_id,
                "document_edit_state": doc.document_edit_state,
            }
            for doc in documents
        ]
        return document_list

    def get_document_by_id(self, document_id):
        return self.__document_repository.get_document_by_id(document_id)

    def save_document(
        self, name: str, content: str, project_id: int, creator_id: int, state_id: int
    ):
        return self.__document_repository.save(
            name, content, project_id, creator_id, state_id
        )


document_service = DocumentService(DocumentRepository(), user_service, token_service)
