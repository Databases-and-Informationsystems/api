from werkzeug.exceptions import BadRequest, Conflict, NotFound, Unauthorized

from app.repositories.team_repository import TeamRepository
from app.services.user_service import UserService, user_service


class TeamService:
    __team_repository: TeamRepository
    user_service: UserService

    def __init__(self, team_repository, user_service):
        self.__team_repository = team_repository
        self.user_service = user_service

    def get_teams_by_user(self):
        user_id = 1  # self.user_service.get_logged_in_user_id()
        teams = self.__team_repository.get_teams_by_user(user_id)
        if teams is None:
            return {"teams": []}
        return {
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "creator_id": team.creator_id,
                    "members": self.__get_team_members_by_team_id(team.id),
                }
                for team in teams
            ]
        }

    def __get_team_members_by_team_id(self, team_id):
        members = self.__team_repository.get_members_of_team(team_id)
        return [
            {"id": member.id, "username": member.username, "email": member.email}
            for member in members
        ]


    def add_user_to_team(self, user_mail, team_id):
        new_member = self.user_service.get_user_by_email(user_mail)

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

    def create_team(self, team_name):
        user_id = 1  # self.user_service.get_logged_in_user_id()

        team = self.__team_repository.create_team(team_name, user_id)
        self.add_user(team.id, user_id)
        return {
            "id": team.id,
            "name": team.name,
            "creator_id": team.creator_id,
        }

    # this will also have user_id for checking the creator and the current user when auth is added
    def delete_team(self, team_id):
        team = self.__team_repository.get_team_by_id(team_id)

        if not team:
            raise NotFound("Team not found.")

        # Check if the logged-in user is the creator
        #if team.creator_id != user_id:
        #    raise Unauthorized("You are not authorized to delete this team.")

        # Delete the team if authorized
        deleted = self.__team_repository.delete_team_by_id(team_id)
        if not deleted:
            raise NotFound("Team not found during deletion.")



team_service = TeamService(TeamRepository(), user_service)
