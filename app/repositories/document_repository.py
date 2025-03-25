import typing

from app.models.buisness_models import BDocument, BDocumentEdit
from app.models.db_models import (
    Document,
    DocumentState,
    Project,
    DocumentEditState,
    DocumentEdit,
    Team,
    User,
    UserTeam,
    Schema,
)
from app.repositories.base_repository import BaseRepository
from sqlalchemy import and_


class DocumentRepository(BaseRepository):
    DOCUMENT_STATE_ID_FINISHED = 3

    def get_documents_by_user(self, user_id) -> typing.List[BDocument]:
        return [
            BDocument.from_db(d)
            for d in (
                self.get_session()
                .query(Document, DocumentEdit)
                .select_from(UserTeam)
                .filter(UserTeam.user_id == user_id)
                .filter(Document.active == True)
                .join(Team, UserTeam.team_id == Team.id)
                .join(Project, Team.id == Project.team_id)
                .join(Document, Project.id == Document.project_id)
                .join(DocumentState, DocumentState.id == Document.state_id)
                .join(Schema, Schema.id == Project.schema_id)
                .join(User, User.id == Document.creator_id)
                .outerjoin(
                    DocumentEdit,
                    and_(
                        Document.id == DocumentEdit.document_id,
                        DocumentEdit.user_id == user_id,
                    ),
                )
                .outerjoin(
                    DocumentEditState, DocumentEditState.id == DocumentEdit.state_id
                )
            ).all()
        ]

    def get_documents_by_project(
        self, project_id: str, user_id: str
    ) -> typing.List[BDocument]:
        return [
            BDocument.from_db(d)
            for d in (
                self.get_session()
                .query(Document)
                .filter(Document.project_id == project_id)
                .filter(Document.active == True)
            )
        ]

    def create_document(self, name, content, project_id, user_id):
        """
        Creates and stores a document in the database.

        Args:
            name (str): Name of the document.
            content (str): Content of the document.
            project_id (int): ID of the associated project.
            user_id (int): ID of the associated creator.

        Returns:
            Document: The created Document object.
        """
        document = Document(
            name=name,
            content=content,
            project_id=project_id,
            creator_id=user_id,
            state_id=1,
        )
        self.store_object(document)
        return document

    def get_document_by_id(self, document_id, user_id) -> typing.Optional[BDocument]:
        document = (
            self.get_session()
            .query(Document)
            .filter(Document.id == document_id)
            .filter(Document.active == True)
            .join(Project, Project.id == Document.project_id)
            .join(Team, Project.team_id == Team.id)
            .join(DocumentState, DocumentState.id == Document.state_id)
            .join(Schema, Schema.id == Project.schema_id)
            .join(User, User.id == Document.creator_id)
            .outerjoin(
                DocumentEdit,
                and_(
                    DocumentEdit.document_id == document_id,
                    DocumentEdit.user_id == user_id,
                ),
            )
            .outerjoin(DocumentEditState, DocumentEditState.id == DocumentEdit.state_id)
        ).first()

        return BDocument.from_db(document) if document else None

    def save(self, name, content, project_id, creator_id, state_id):
        document = Document(
            name=name,
            content=content,
            project_id=project_id,
            creator_id=creator_id,
            state_id=state_id,
            active=True,
        )
        return super().store_object(document)

    def soft_delete_document(self, document_id: int):
        document = (
            self.get_session()
            .query(Document)
            .filter(Document.id == document_id, Document.active == True)
            .first()
        )
        if not document:
            return False

        document.active = False
        return True

    def bulk_soft_delete_documents_by_project_id(self, project_id: int) -> list[int]:
        # Step 1: Get all doc IDs first
        doc_ids = (
            self.get_session()
            .query(Document.id)
            .filter(Document.project_id == project_id, Document.active == True)
            .all()
        )  # returns list of tuples like [(1,), (2,)...]
        doc_ids = [row[0] for row in doc_ids]

        if not doc_ids:
            return []

        # Step 2: Bulk update
        self.get_session().query(Document).filter(Document.id.in_(doc_ids)).update(
            {Document.active: False}, synchronize_session=False
        )

        return doc_ids

    def get_all_document_edits_by_document(self, document_id):
        return (
            self.get_session()
            .query(DocumentEdit)
            .filter(DocumentEdit.document_id == document_id)
            .filter(DocumentEdit.active == True)
            .all()
        )

    def get_all_document_edits_with_user_by_document(self, document_id):
        return [
            BDocumentEdit.from_db(de)
            for de in (
                self.get_session()
                .query(DocumentEdit)
                .join(User, User.id == DocumentEdit.user_id)
                .join(DocumentEditState, DocumentEditState.id == DocumentEdit.state_id)
                .filter(DocumentEdit.document_id == document_id)
                .filter(DocumentEdit.active == True)
                .all()
            )
        ]

    def update_document_state(self, document_id, new_state_id):
        """
        Update the state of a document in the database.
        """
        session = self.get_session()
        document = session.query(Document).filter(Document.id == document_id).first()
        if document:
            document.state_id = new_state_id
        self.store_object(document)
        return document

    def get_document_state_by_id(self, state_id):
        return (
            self.get_session()
            .query(DocumentState)
            .filter(DocumentState.id == state_id)
            .first()
        )
