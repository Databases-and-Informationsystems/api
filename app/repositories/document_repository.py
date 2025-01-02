from app.models import (
    Document,
    DocumentState,
    Project,
    DocumentEditState,
    DocumentEdit,
    Team,
    User,
    UserTeam,
    DocumentRecommendation,
)
from app.repositories.base_repository import BaseRepository
from sqlalchemy import exc, and_
from app.db import db


class DocumentRepository(BaseRepository):
    def get_documents_by_user(self, user_id):
        return (
            db.session.query(
                Document.id,
                Document.content,
                Document.name,
                Document.project_id,
                Project.name.label("project_name"),
                Project.schema_id,
                Team.name.label("team_name"),
                Team.id.label("team_id"),
                DocumentEditState.type.label("document_edit_state"),
                DocumentEdit.id.label("document_edit_id"),
            )
            .select_from(User)
            .filter(User.id == user_id)
            .join(UserTeam, User.id == UserTeam.user_id)
            .join(Team, UserTeam.team_id == Team.id)
            .join(Project, Team.id == Project.team_id)
            .join(Document, Project.id == Document.project_id)
            .join(DocumentState, DocumentState.id == Document.state_id)
            .outerjoin(
                DocumentEdit,
                and_(
                    Document.id == DocumentEdit.document_id,
                    DocumentEdit.user_id == user_id,
                ),
            )
            .outerjoin(DocumentEditState, DocumentEditState.id == DocumentEdit.state_id)
        )

    def get_document_by_id(self, document_id):
        return (
            db.session.query(
                Document.content,
                Document.name,
                Document.project_id,
                Project.name.label("project_name"),
                Project.schema_id,
                Project.team_id,
                DocumentRecommendation.id.label("document_recommendation_id"),
            )
            .select_from(Document)
            .filter(Document.id == document_id)
            .join(Project, Project.id == Document.project_id)
            .outerjoin(
                DocumentRecommendation,
                and_(
                    Document.id == DocumentRecommendation.document_id,
                    DocumentRecommendation.document_edit_id is None,
                ),
            )
        ).first()
