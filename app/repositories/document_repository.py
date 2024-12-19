from app.models import (
    Document,
    DocumentState,
    Project,
    DocumentEditState,
    DocumentEdit,
    Team,
    User,
    UserTeam,
)
from app.repositories.base_repository import BaseRepository
from sqlalchemy import exc, and_
from app.db import db


class DocumentRepository(BaseRepository):
    def get_documents_by_project(self, project_id):
        return (
            db.session.query(
                Document.id,
                Document.content,
                Document.name,
                Document.project_id,
                DocumentState.type,
                Project.name.label("project_name"),
            )
            .join(Project)
            .join(DocumentState)
            .filter(Document.project_id == project_id)
        ).all()

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
