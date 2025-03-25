import typing

from app.models.buisness_models import BProject
from app.models.db_models import Project, Document, DocumentEdit, Team, UserTeam, Schema
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository):

    def create_project(self, name, creator_id, team_id, schema_id):
        project = Project(
            name=name,
            creator_id=creator_id,
            team_id=team_id,
            schema_id=schema_id,
            active=True,
        )
        super().store_object(project)
        return project

    def get_team_id_by_document_edit_id(self, document_edit_id):
        project = (
            self.get_session()
            .query(Project)
            .join(Document, Document.project_id == Project.id)
            .join(DocumentEdit, DocumentEdit.document_id == Document.id)
            .filter(DocumentEdit.id == document_edit_id)
            .first()
        )
        return project.team_id

    def get_projects_by_team(self, team_id):
        return (
            self.get_session()
            .query(Project)
            .filter(Project.team_id == team_id)
            .filter(Project.active == True)
            .all()
        )

    def get_project_by_id(self, project_id) -> typing.Optional[BProject]:
        project = (
            self.get_session()
            .query(
                Project,
            )
            .select_from(UserTeam)
            .join(Team, Team.id == UserTeam.team_id)
            .join(Project, Project.team_id == Team.id)
            .filter(Project.id == project_id)
            .filter(Project.active == True)
            .first()
        )
        return BProject.from_db(project) if project else None

    def get_projects_by_user(self, user_id) -> typing.List[BProject]:
        return [
            BProject.from_db(project)
            for project in (
                self.get_session()
                .query(
                    Project,
                )
                .select_from(UserTeam)
                .join(Team, Team.id == UserTeam.team_id)
                .join(Project, Project.team_id == Team.id)
                .filter(UserTeam.user_id == user_id)
                .filter(Project.active == True)
                .all()
            )
        ]

    def soft_delete_project(self, project_id):
        project = (
            self.get_session()
            .query(Project)
            .filter(Project.id == project_id, Project.active == True)
            .first()
        )
        if not project:
            return False

        project.active = False
        return True

    def get_project_by_name(self, name):
        return (
            self.get_session()
            .query(Project)
            .filter(Project.name == name)
            .filter(Project.active == True)
            .first()
        )
