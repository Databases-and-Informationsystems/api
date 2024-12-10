from werkzeug.exceptions import NotFound, Forbidden, InternalServerError

from app.repositories.document_repository import DocumentRepository
from app.services.user_service import UserService, user_service
from app.services.team_service import TeamService, team_service
from app.services.project_service import ProjectService, project_service


class DocumentService:
    __document_repository: DocumentRepository
    user_service: UserService

    def __init__(self, document_repository, user_service):
        self.__document_repository = document_repository
        self.user_service = user_service
        self.team_service = team_service
        self.project_service = project_service

    def get_documents_by_project(self, project_id):
        return self.__document_repository.get_documents_by_project(project_id)

    def get_documents_by_user(self, user_id):
        self.user_service.check_authentication(user_id)
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
                "type": doc.type,
                "team_name": doc.team_name,
                "team_id": doc.team_id,
                "document_edit_id": doc.document_edit_id,
                "document_edit_state": doc.document_edit_state,
            }
            for doc in documents
        ]
        return document_list, 200


document_service = DocumentService(DocumentRepository(), user_service)


class DocumentService:
    def __init__(self, document_repository: DocumentRepository, project_service):
        """
        Initializes the DocumentService with required dependencies.
        :param document_repository: Instance of the associated repository
        :param project_service: Instance of the ProjectService
        """
        self.document_repository = document_repository
        self.project_service = project_service

    def upload_document(self, user_id, project_id, document_name, document_content):
        """
        Uploads a document after verifying the user's membership in the project.
        :param user_id: ID of the user
        :param project_id: ID of the project
        :param document_name: Name of the document
        :param document_content: Content of the document
        :return: The created document (with ID and other details)
        :raises Forbidden: If the user is not allowed to upload the document
        :raises InternalServerError: If an error occurs while saving the document
        """
        # Verify user's membership in the project
        if not self.project_service.is_user_in_project(user_id, project_id):
            raise Forbidden("User is not authorized to upload this document.")

        # Prepare document data
        document_data = {
            "name": document_name,
            "content": document_content,
            "creator_id": user_id,
            "project_id": project_id,
        }

        # Save the document and return it
        try:
            return self.document_repository.create_document(document_data)
        except Exception as e:
            raise InternalServerError(f"Error saving the document: {str(e)}")

