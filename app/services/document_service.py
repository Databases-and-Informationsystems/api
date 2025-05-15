from werkzeug.exceptions import BadRequest, NotFound
from app.repositories.document_repository import DocumentRepository
from app.services.document_edit_service import (
    document_edit_service,
    DocumentEditService,
)
from app.services.scope_service import scope_service, ScopeService
from app.services.token_service import TokenService, token_service


class DocumentService:
    __document_repository: DocumentRepository
    token_service: TokenService
    document_edit_service: DocumentEditService
    scope_service: ScopeService

    def __init__(
        self,
        document_repository,
        token_service,
        document_edit_service,
        scope_service,
    ):
        self.__document_repository = document_repository
        self.token_service = token_service
        self.document_edit_service = document_edit_service
        self.scope_service = scope_service

    def get_documents_by_project(self, user_id, project_id):
        """
        Fetch all documents of a project the user has access to.
        Documents also contain list of users which have annotated this document.

        :param user_id: User ID with access to the project.
        :param project_id: Project ID to query documents
        :return: document_list_dto
        """
        response = self.get_documents_by_user(user_id)
        documents = response["documents"]
        filtered_documents = [
            document
            for document in documents
            if document["project"]["id"] == project_id
        ]
        return {"documents": filtered_documents}

    def get_documents_by_user(self, user_id):
        """
        Fetch all documents the user has access to.
        Documents also contain list of users which have annotated this document.

        :param user_id: User ID to query documents for.
        :return: document_list_dto
        """
        documents = self.__document_repository.get_documents_by_user(user_id)
        document_list = [self.__map_document_to_output_dto(doc) for doc in documents]
        return {"documents": document_list}

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

    def get_document_by_id(self, document_id, user_id):
        """
        Fetch a document by its ID.
        Document also contains list of users which have annotated this document.

        :param user_id: User ID to query the document for.
        :param document_id: Document ID to query.
        :return: document_output_dto
        :raises NotFound: If the document does not exist.
        """
        document = self.__document_repository.get_document_by_id(document_id, user_id)
        if not document:
            raise NotFound("Document not found")
        return self.__map_document_to_output_dto(document)

    def save_document(
        self, name: str, content: str, project_id: int, creator_id: int, state_id: int
    ):
        """
        Save a document in the database.
        Does not check for valid inputs.

        :param name: Name of the document.
        :param content: Content of the document.
        :param project_id: Project ID of the document.
        :param creator_id: Creator ID of the document.
        :param state_id: State ID of the document.
        :return: Newly created document.
        """
        return self.__document_repository.save(
            name, content, project_id, creator_id, state_id
        )

    def soft_delete_document(self, document_id: int):
        if not isinstance(document_id, int) or document_id <= 0:
            raise BadRequest("Invalid document ID. Must be a positive integer.")

        success = self.__document_repository.soft_delete_document(document_id)
        if not success:
            raise NotFound("Document not found or already inactive.")

        self.document_edit_service.soft_delete_edits_for_document(document_id)

        return {"message": "Document set to inactive successfully."}

    def bulk_soft_delete_documents_by_project_id(self, project_id):
        document_ids = (
            self.__document_repository.bulk_soft_delete_documents_by_project_id(
                project_id
            )
        )

        if document_ids:
            self.document_edit_service.bulk_soft_delete_edits_for_documents(
                document_ids
            )

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
        document_edits = (
            self.__document_repository.get_all_document_edits_with_user_by_document(
                document_id
            )
        )

        processed_edits = [
            {
                "id": edit.edit_id,
                "user": {
                    "id": edit.user_id,
                    "email": edit.user_email,
                    "username": edit.user_username,
                },
                "state": {
                    "id": edit.state_id,
                    "type": edit.state_type,
                },
            }
            for edit in document_edits
        ]

        return processed_edits

    def __map_document_to_output_dto(self, doc):
        """
        Maps input document to output dto.

        :param doc: Document to map.
        :return: document_output_dto
        """
        return {
            "id": doc.id,
            "content": doc.content,
            "name": doc.name,
            "state": {
                "id": doc.document_state_id,
                "type": doc.document_state_type,
            },
            "project": {
                "id": doc.project_id,
                "name": doc.project_name,
            },
            "schema": {
                "id": doc.schema_id,
                "name": doc.schema_name,
            },
            "team": {
                "id": doc.team_id,
                "name": doc.team_name,
            },
            "document_edit": {
                "id": doc.document_edit_id,
                "state": doc.document_edit_state,
            },
            "document_edits": self.get_all_document_edits_with_user_by_document(doc.id),
            "creator": {
                "id": doc.creator_id,
                "username": doc.username,
                "email": doc.email,
            },
        }

    def change_document_state(self, document_id, new_state_id, user_id):
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

    def get_scope_interpretations(
        self,
        user_id,
        document_id,
        model,
        num_interpretations,
        pass_interpretations,
        temperature,
        with_text,
        bottom_up,
    ):
        document = self.get_document_by_id(document_id, user_id)
        scope_interpretations = self.scope_service.get_scope_interpretations(
            document["id"],
            document["content"],
            model,
            num_interpretations,
            temperature,
            pass_interpretations,
            with_text,
            bottom_up,
        )

        saved_interpretations = []
        for interpretation in scope_interpretations:
            doc_edit = self.document_edit_service.create_document_edit(
                user_id, document_id
            )
            scope_tree = self.scope_service.save_scope_recommendations(
                doc_edit["id"], interpretation
            )
            saved_interpretations.append(scope_tree)
        return saved_interpretations


document_service = DocumentService(
    DocumentRepository(), token_service, document_edit_service, scope_service
)
