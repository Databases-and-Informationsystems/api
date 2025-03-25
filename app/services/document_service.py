import typing

from werkzeug.exceptions import BadRequest, NotFound

from app.models.buisness_models import BDocument
from app.repositories.document_repository import DocumentRepository
from app.services.token_service import TokenService, token_service


class DocumentService:
    __document_repository: DocumentRepository
    token_service: TokenService

    def __init__(
        self,
        document_repository,
        token_service,
    ):
        self.__document_repository = document_repository
        self.token_service = token_service

    def get_documents_by_project(
        self, user_id: str, project_id: str
    ) -> typing.List[BDocument]:
        """
        Fetch all documents of a project the user has access to.
        Documents also contain list of users which have annotated this document.

        :param user_id: User ID with access to the project.
        :param project_id: Project ID to query documents
        :return: document_list_dto
        """
        documents = self.__document_repository.get_documents_by_project(
            project_id, user_id
        )
        documents = [
            d.with_document_edits(
                self.get_all_document_edits_with_user_by_document(d.id)
            )
            for d in documents
        ]
        return documents

    def get_documents_by_user(self, user_id) -> typing.List[BDocument]:
        """
        Fetch all documents the user has access to.
        Documents also contain list of users which have annotated this document.

        :param user_id: User ID to query documents for.
        :return: document_list_dto
        """
        documents = self.__document_repository.get_documents_by_user(user_id)
        documents = [
            d.with_document_edits(
                self.get_all_document_edits_with_user_by_document(d.id)
            )
            for d in documents
        ]
        return documents

    def upload_document(self, user_id, project_id, file_name, file_content):
        # Validate file content
        if not file_name or not file_content.strip():
            raise ValueError("Invalid file content or file name.")

        # Store the document
        document = self.__document_repository.create_document(
            name=file_name, content=file_content, project_id=project_id, user_id=user_id
        )

        # Tokenize document
        self.token_service.tokenize_document(document.id, document.content)
        return self.get_document_by_id(document.id, user_id)

    def get_document_by_id(
        self, document_id: int, user_id: int, with_tokens=False
    ) -> BDocument:
        document = self.__document_repository.get_document_by_id(document_id, user_id)
        if not document:
            raise NotFound("Document not found")

        if with_tokens:
            document.tokens = self.token_service.get_tokens_by_document(document.id)
        return document

    def save_document(
        self, name: str, content: str, project_id: int, creator_id: int, state_id: int
    ):
        return self.__document_repository.save(
            name, content, project_id, creator_id, state_id
        )

    def soft_delete_document(self, document_id: int) -> None:
        if not isinstance(document_id, int) or document_id <= 0:
            raise BadRequest("Invalid document ID. Must be a positive integer.")

        success = self.__document_repository.soft_delete_document(document_id)
        if not success:
            raise NotFound("Document not found or already inactive.")

        # TODO document_edits should be deleted as well
        # TODO Resolve Circular dependency
        # self.document_edit_service.soft_delete_edits_for_document(document_id)

    def bulk_soft_delete_documents_by_project_id(self, project_id):
        document_ids = (
            self.__document_repository.bulk_soft_delete_documents_by_project_id(
                project_id
            )
        )

        # TODO document_edits should be deleted as well
        # TODO Resolve Circular dependency
        # if document_ids:
        #     self.document_edit_service.bulk_soft_delete_edits_for_documents(
        #        document_ids
        #    )

    def get_all_structured_document_edits_by_document(self, document_id):
        document_edits = self.__document_repository.get_all_document_edits_by_document(
            document_id
        )
        if not document_edits:
            raise NotFound("No DocumentEdits found for document ID")

        transformed_edits = [
            self.document_edit_service.get_document_edit_by_id_for_difference_calc(
                document_edit.id
            )
            for document_edit in document_edits
        ]

        return transformed_edits

    def get_all_document_edits_with_user_by_document(self, document_id):
        return self.__document_repository.get_all_document_edits_with_user_by_document(
            document_id
        )

    def change_document_state(self, document_id, new_state_id, user_id) -> BDocument:
        """
        Change the state of a document after validating the input and user access.
        """
        # Validate the new state
        state = self.__document_repository.get_document_state_by_id(new_state_id)
        if not state:
            raise BadRequest("Invalid document state")

        # Update the document state
        document = self.__document_repository.update_document_state(
            document_id, new_state_id
        )
        if not document:
            raise BadRequest("Document not found")

        # Return the updated document in correct response format
        return self.get_document_by_id(document.id, user_id)


document_service = DocumentService(
    DocumentRepository(),
    token_service,
)
