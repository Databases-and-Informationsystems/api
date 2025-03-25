import typing

from werkzeug.exceptions import BadRequest, NotFound

from app.models.buisness_models import BProject
from app.services.schema_service import SchemaService, schema_service
from app.services.user_service import (
    UserService,
    user_service,
)
from app.repositories.project_repository import ProjectRepository
from app.services.document_service import DocumentService, document_service


class ProjectService:
    __project_repository: ProjectRepository
    user_service: UserService
    schema_service: SchemaService
    document_service: DocumentService

    def __init__(
        self,
        project_repository,
        user_service,
        schema_service,
        document_service,
    ):
        self.__project_repository = project_repository
        self.user_service = user_service
        self.schema_service = schema_service
        self.document_service = document_service

    def create_project(self, user_id, team_id, schema_id, projectname):
        """
        Creates a new project with the given parameters.
        Sets schema as fixed and not modifiable.

        :param user_id: Creator ID of the project
        :param team_id: Team ID of the project
        :param schema_id: Schema ID of the project
        :param projectname: Name of the project
        :return: project_output_dto
        :raises BadRequest: If project name already exists
        """
        duplicate_project = self.__project_repository.get_project_by_name(projectname)
        if duplicate_project:
            raise BadRequest("Project with name " + projectname + " already exists")

        self.schema_service.fix_schema(schema_id)
        project = self.__project_repository.create_project(
            projectname,
            user_id,
            team_id,
            schema_id,
        )
        return self.get_project_by_id(project.id)

    def team_is_in_project(self, team_id, document_edit_id):
        return team_id == self.__project_repository.get_team_id_by_document_edit_id(
            document_edit_id
        )

    def get_project_by_id(self, project_id) -> BProject:
        """
        Fetches project by project ID

        :param project_id: Project ID to query.
        :return: BProject
        :raises BadRequest: If project does not exist
        """
        project = self.__project_repository.get_project_by_id(project_id)

        if project is None:
            raise BadRequest("Project not found")
        return project

    def get_projects_by_user(self, user_id) -> typing.List[BProject]:
        """

        :param user_id:
        :return:
        """
        return self.__project_repository.get_projects_by_user(user_id)

    def __build_project(self, project):
        """
        Maps project to output dto.

        :param project: Project to map.
        :return: project_output_dto
        """
        return {
            "id": project.id,
            "name": project.name,
            "creator": self.user_service.get_user_by_id(project.creator_id),
            "team": {
                "id": project.team_id,
                "name": project.team_name,
            },
            "schema": {
                "id": project.schema_id,
                "name": project.schema_name,
            },
        }

    def soft_delete_project(self, project_id):
        if not isinstance(project_id, int) or project_id <= 0:
            raise BadRequest("Invalid project ID. Must be a positive integer.")

        success = self.__project_repository.soft_delete_project(project_id)
        if not success:
            raise NotFound("Project not found or already inactive.")

        self.document_service.bulk_soft_delete_documents_by_project_id(project_id)

    def get_projects_by_team(self, team_id):
        projects = self.__project_repository.get_projects_by_team(team_id)
        return projects


project_service = ProjectService(
    ProjectRepository(), user_service, schema_service, document_service
)
