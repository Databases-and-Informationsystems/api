from flask import session
from werkzeug.exceptions import BadRequest, Forbidden

from app.repositories.user_repository import UserRepository
from app.repositories.user_team_repository import UserTeamRepository


class UserService:
    __user_repository: UserRepository
    user_team_repository: UserTeamRepository

    def __init__(self, user_repository, user_team_repository):
        self.__user_repository = user_repository
        self.user_team_repository = user_team_repository

    @staticmethod
    def check_authentication(user_id):
        if "user_id" not in session or user_id != session["user_id"]:
            raise Forbidden("You need to be logged in")

    def check_user_in_team(self, user_id, team_id):
        if self.__user_repository.check_user_in_team(user_id, team_id) is None:
            raise BadRequest("You have to be in a team")

    def get_logged_in_user_id(self):
        if "user_id" not in session or session["user_id"] is None:
            raise Forbidden("You need to be logged in")
        return session["user_id"]

    def get_logged_in_user_team_id(self):
        return self.user_team_repository.get_user_team_id(self.get_logged_in_user_id())

    def get_user_by_document_edit_id(self, document_edit_id):
        return self.__user_repository.get_user_by_document_edit_id(document_edit_id)


user_service = UserService(UserRepository(), UserTeamRepository())
