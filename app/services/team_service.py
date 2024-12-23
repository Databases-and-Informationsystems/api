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

    def create_team(self, team_name):
        user_id = 1  # self.user_service.get_logged_in_user_id()

        team = self.__team_repository.create_team(team_name, user_id)
        self.add_user(team.id, user_id)
        return {
            "id": team.id,
            "name": team.name,
            "creator_id": team.creator_id,
        }

    def add_user(self, team_id, user_id):
        return self.__team_repository.add_user(team_id, user_id)


team_service = TeamService(TeamRepository(), user_service)
