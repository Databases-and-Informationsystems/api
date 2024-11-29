from app.models import UserTeam
from app.repositories.base_repository import BaseRepository
from app.db import db


class UserRepository(BaseRepository):
    def check_user_in_team(self, user_id, team_id):
        if (
            db.session.query(UserTeam)
            .filter(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
            .first()
            is None
        ):
            response = {"message": "User not in team"}
            return response, 400
        return "", 200