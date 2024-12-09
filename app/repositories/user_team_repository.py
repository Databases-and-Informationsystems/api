from app.models import UserTeam
from app.repositories.base_repository import BaseRepository
from app.db import db


class UserTeamRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def get_user_team_id(self, user_id):
        user_team = (
            db.session.query(UserTeam).filter(UserTeam.user_id == user_id).first()
        )
        return user_team.team_id
