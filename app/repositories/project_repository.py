from app.models import Project, Document, DocumentEdit, Team, UserTeam
from app.repositories.base_repository import BaseRepository
from sqlalchemy import exc
from app.db import db


class ProjectRepository(BaseRepository):
    def create_project(self, name, creator_id, team_id, schema_id):
        project = Project(
            name=name,
            creator_id=creator_id,
            team_id=team_id,
            schema_id=schema_id,
        )
        super().store_object(project)
        return project


    def get_team_id_by_document_edit_id(self, document_edit_id):
        project = (
            db.session.query(Project)
            .join(Document, Document.project_id == Project.id)
            .join(DocumentEdit, DocumentEdit.document_id == Document.id)
            .filter(DocumentEdit.id == document_edit_id)
            .first()
        )
        return project.team_id

    def get_projects_by_team(self, team_id):
        return db.session.query(Project).filter(Project.team_id == team_id).all()


def get_project_for_user(project_id, user_id):
    """
     ein Benutzer Mitglied des Teams, das ein bestimmtes Projekt besitzt?

    :param project_id: Die ID des Projekts
    :param user_id: Die ID des Benutzers
    :return: Das Projektobjekt, falls es gefunden wird, sonst None
    """
    return (
        db.session.query(Project)
        .filter_by(id=project_id)
        .join(Team, Team.id == Project.team_id)
        .join(UserTeam, UserTeam.team_id == Team.id)
        .filter(UserTeam.user_id == user_id)
        .first()
    )
    
