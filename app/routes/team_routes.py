import typing
from flask_restx import Namespace
from flask import request
from werkzeug.exceptions import Forbidden

from app.dtos import (
    team_input_dto,
    team_member_input_dto,
    team_output_dto,
)
from app.models.buisness_models import BTeam
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.team_service import team_service, TeamService

ns = Namespace("teams", description="Team related operations")


class TeamBaseRoute(AuthorizedBaseRoute):
    service: TeamService = team_service


@ns.route("/<int:team_id>/members")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TeamMembersRoutes(TeamBaseRoute):

    @ns.expect(team_member_input_dto)
    @ns.marshal_with(team_output_dto)
    def post(self, team_id):
        """
        Add a user to a team
        """
        request_data = request.get_json()

        user = self.user_service.get_user_id()
        self.user_service.check_user_in_team(user, team_id)

        team = self.service.add_user_to_team(
            request_data["user_mail"],
            team_id,
        )
        return team.to_json()


@ns.route("/<int:team_id>/members/<int:user_id>")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TeamMembersRoutes(TeamBaseRoute):

    @ns.marshal_with(team_output_dto)
    def delete(self, team_id, user_id):
        """
        Remove a user from a team
        """

        self.user_service.check_user_in_team(self.user_service.get_user_id(), team_id)

        team = self.service.remove_user_from_team(
            user_id,
            team_id,
        )
        return team.to_json()


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TeamRoutes(TeamBaseRoute):

    @ns.marshal_with(team_output_dto, as_list=True)
    def get(self):
        """
        Fetch all teams user has access to
        """
        user_id = self.user_service.get_user_id()

        teams: typing.List[BTeam] = self.service.get_by_user(user_id)
        return [team.to_json() for team in teams]

    @ns.expect(team_input_dto)
    @ns.marshal_with(team_output_dto)
    def post(self):
        """
        Create a new team
        """
        request_data = request.get_json()

        user_id = self.user_service.get_user_id()

        team = self.service.create_team(
            user_id,
            request_data["name"],
        )
        return team.to_json()


@ns.route("/<int:team_id>")
@ns.response(404, "Team not found")
class TeamUpdateResource(TeamBaseRoute):
    """API endpoint to update team properties."""

    @ns.marshal_with(team_output_dto)
    def get(self, team_id):
        user_id = self.user_service.get_user_id()
        if not self.user_service.is_user_in_team(user_id, team_id):
            raise Forbidden("User is not a member of the requested Team")

        return self.service.get_by_id(team_id).to_json()

    @ns.expect(team_input_dto)
    @ns.marshal_with(team_output_dto)
    def put(self, team_id):
        """Update the name of a team."""
        data = request.json

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_in_team(user_id, team_id)

        team = self.service.update_team_name(team_id, data["name"])
        return team.to_json()
