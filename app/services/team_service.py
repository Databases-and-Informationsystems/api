from werkzeug.exceptions import BadRequest, Conflict

from app.repositories.team_repository import TeamRepository
from app.services.user_service import UserService, user_service


class TeamService:
    __team_repository: TeamRepository
    user_service: UserService

    def __init__(self, team_repository, user_service):
        self.__team_repository = team_repository
        self.user_service = user_service

    def get_teams_by_user(self, user_id):
        return self.__team_repository.get_teams_by_user(user_id)

    def add_user_to_team(self, user_mail, team_id):
        new_member = self.user_service.get_user_by_mail(user_mail)

        # If user does not exist, raise exception
        if new_member is None:
            raise BadRequest("User not found")

        # Check if logged-in user is part of the team
        user = 1  # self.user_service.get_logged_in_user_id()
        self.user_service.check_user_in_team(user, team_id)

        # Check that new member is not already part of the team
        try:
            self.user_service.check_user_in_team(new_member.id, team_id)
            raise Conflict("User is already part of the team")
        except BadRequest:
            self.add_user(team_id, new_member.id)
            return {
                "id": new_member.id,
                "username": new_member.username,
                "email": new_member.email,
            }

    def add_user(self, team_id, user_id):
        return self.__team_repository.add_user(team_id, user_id)


team_service = TeamService(TeamRepository(), user_service)
