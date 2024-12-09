from app.repositories.document_edit_repository import DocumentEditRepository


class DocumentEditService:
    __document_edit_repository: DocumentEditRepository

    def __init__(self, document_edit_repository: DocumentEditRepository):
        self.__document_edit_repository = document_edit_repository

    def get_user_id(self, id):
        return self.__document_edit_repository.get_user_id(id)


document_edit_service = DocumentEditService(DocumentEditRepository())
