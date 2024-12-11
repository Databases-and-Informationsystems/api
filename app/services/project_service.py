from app.services.schema_service import SchemaService, schema_service
from app.services.user_service import (
    UserService,
    user_service,
)
from app.repositories.project_repository import ProjectRepository
from app.services.team_service import TeamService, team_service


class ProjectService:
    user_service: UserService
    schema_service: SchemaService

    __project_repository: ProjectRepository

    def __init__(self, project_repository, user_service, schema_service):
        self.__project_repository = project_repository
        self.user_service = user_service
        self.schema_service = schema_service

    def create_project(self, team_id, schema_id, projectname):
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_in_team(user_id, team_id)
        self.schema_service.check_schema_exists(schema_id)
        project = self.__project_repository.create_project(
            projectname,
            user_id,
            team_id,
            schema_id,
        )
        return {
            "id": project.id,
            "name": project.name,
            "team_id": project.team_id,
            "schema_id": project.schema_id,
            "creator_id": project.creator_id,
        }

    def team_is_in_project(self, team_id, document_edit_id):
        return team_id == self.__project_repository.get_team_id_by_document_edit_id(
            document_edit_id
        )


project_service = ProjectService(ProjectRepository(), user_service, schema_service)
