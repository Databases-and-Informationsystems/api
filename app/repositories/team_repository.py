from app.models import UserTeam, Team
from app.repositories.base_repository import BaseRepository
from app.db import db


class TeamRepository(BaseRepository):

    def get_teams_by_user(self, user_id):
        return (
            db.session.query(Team)
            .join(UserTeam)
            .filter(UserTeam.user_id == user_id)
            .all()
        )

    def add_user(self, team_id, user_id):
        userteam = UserTeam(team_id=team_id, user_id=user_id)
        super().store_object(userteam)
        return userteam
