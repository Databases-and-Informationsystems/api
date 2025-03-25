import typing

from werkzeug.exceptions import BadRequest, Conflict, NotFound, Forbidden

from app.models.buisness_models import BTeam
from app.repositories.team_repository import TeamRepository
from app.services.user_service import UserService, user_service
from app.services.project_service import project_service, ProjectService


class TeamService:
    __team_repository: TeamRepository
    _user_service: UserService
    _project_service: ProjectService

    def __init__(self, team_repository, user_svc, project_svc):
        self.__team_repository = team_repository
        self._user_service = user_svc
        self._project_service = project_svc

    def get_by_user(self, user_id) -> typing.List[BTeam]:
        """
        Fetches all teams a user has access to

        :param user_id: User ID to query.
        :return: team_user_output_list_dto
        """
        return self.__team_repository.get_teams_by_user(user_id)

    def get_by_id(self, team_id) -> typing.Optional[BTeam]:
        """
        Fetch team by team ID

        :param team_id: Team ID to query.
        :return: team_user_output_dto
        """
        return self.__team_repository.get_team_by_id(team_id)

    def add_user_to_team(self, user_mail: str, team_id: int) -> typing.Optional[BTeam]:
        """
        Adds user to a team
        :param user_mail: Email of user to add
        :param team_id: Team ID
        :return: team_user_output_dto
        :raises NotFound: If user does not exist
        :raises Conflict: If user already member of the team
        """
        new_member = self._user_service.get_user_by_email(user_mail)

        if new_member is None or new_member.id is None:
            raise NotFound("User not found")

        if self._user_service.is_user_in_team(new_member.id, team_id):
            raise Conflict("User already member")

        self.__add_user(team_id, new_member.id)
        return self.get_by_id(team_id)

    def __add_user(self, team_id: int, user_id: int) -> None:
        """
        Adds user to team, without validating inputs.

        :param team_id: Team ID to add user to
        :param user_id: user ID to add
        :return: None
        """
        return self.__team_repository.add_user(team_id, user_id)

    def create_team(self, creator_id: int, team_name: str) -> typing.Optional[BTeam]:
        """
        Creates a new team and sets creator as member.

        :param creator_id: Creator ID of the team
        :param team_name: Name of the new team
        :return: team_user_output_dto
        :raises BadRequest: If team name already exists
        """
        duplicate_team = self.__team_repository.get_team_by_name(team_name)
        if duplicate_team:
            raise BadRequest("Team with name " + team_name + " already exists")

        team = self.__team_repository.create_team(team_name, creator_id)
        self.__add_user(team.id, creator_id)
        return self.get_by_id(team.id)

    def remove_user_from_team(
        self, user_id: int, team_id: int
    ) -> typing.Optional[BTeam]:
        """
        Remove user from a team.

        :param user_id: Email of user to delete
        :param team_id: Team ID to remove user from
        :return: team_user_output_dto
        :raises NotFound: If user does not exist
        :raises BadRequest: If user is not part of the team
        """

        # Check that member is currently part of the team
        try:
            self._user_service.check_user_in_team(user_id, team_id)
        except Forbidden:
            raise BadRequest("User is not part of the team")

        self.__team_repository.remove_user(team_id, user_id)
        return self.get_by_id(team_id)

    def get_team_by_project_id(self, project_id):
        if not isinstance(project_id, int) or project_id <= 0:
            raise BadRequest("Invalid project ID. Must be a positive integer.")

        team_id = self.__team_repository.get_by_project_id(project_id)
        if not team_id:
            raise NotFound("No team found for this project or project doesn't exist.")
        return team_id

    def update_team_name(self, team_id: int, new_name: str) -> typing.Optional[BTeam]:
        """Update the name of a team."""
        if not new_name or not new_name.strip():
            raise BadRequest("Team name cannot be empty.")

        updated = self.__team_repository.update_team_name(team_id, new_name)
        if not updated:
            raise NotFound(f"Team with ID {team_id} not found.")
        return self.get_by_id(team_id)


team_service = TeamService(TeamRepository(), user_service, project_service)
