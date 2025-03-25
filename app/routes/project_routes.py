from flask_restx import Namespace
from flask import request

from app.routes.base_routes import AuthorizedBaseRoute
from app.services.project_service import project_service, ProjectService
from app.dtos import (
    project_input_dto,
    project_output_dto,
)

ns = Namespace("projects", description="Project related operations")


class ProjectBaseRoute(AuthorizedBaseRoute):
    service: ProjectService = project_service


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ProjectRoutes(ProjectBaseRoute):

    @ns.expect(project_input_dto)
    @ns.marshal_with(project_output_dto)
    def post(self):
        """
        Create a new project.
        Sets schema as fixed and not modifiable.
        """
        request_data = request.get_json()

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_in_team(user_id, request_data["team"]["id"])
        self.user_service.check_user_schema_accessible(
            user_id, request_data["schema"]["id"]
        )

        project = self.service.create_project(
            user_id,
            request_data["team"]["id"],
            request_data["schema"]["id"],
            request_data["name"],
        )

        return project.to_json()

    @ns.marshal_with(project_output_dto, as_list=True)
    def get(self):
        """
        Fetch all projects the user has access to.
        """
        user_id = self.user_service.get_user_id()

        projects = self.service.get_projects_by_user(user_id)
        return [p.to_json() for p in projects]


@ns.route("/<int:project_id>")
@ns.doc(params={"project_id": "Project ID to soft-delete"})
@ns.response(404, "Project not found")
class ProjectDeletionResource(ProjectBaseRoute):

    @ns.response(204, "Successfully soft deleted project")
    @ns.doc(description="Soft-delete a Project by setting 'active' to False")
    def delete(self, project_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        self.service.soft_delete_project(project_id)
        return "", 204

    @ns.marshal_with(project_output_dto)
    def get(self, project_id):
        """
        Fetch all projects the user has access to.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        project = self.service.get_project_by_id(project_id)
        return project.to_json()
