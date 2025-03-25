import typing

from app.models.buisness_models import BTeam
from app.models.db_models import UserTeam, Team, User, Project
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository):

    def get_teams_by_user(self, user_id) -> typing.List[BTeam]:
        return [
            BTeam.from_db(team)
            for team in (
                self.get_session()
                .query(Team)
                .join(UserTeam, UserTeam.team_id == Team.id)
                .filter(UserTeam.user_id == user_id)
                .filter(Team.active == True)
                .all()
            )
        ]

    def get_team_by_id(self, team_id) -> typing.Optional[BTeam]:
        team = (
            self.get_session()
            .query(Team)
            .filter(Team.id == team_id)
            .filter(Team.active == True)
            .first()
        )
        if team is None:
            return None
        return BTeam.from_db(team)

    def create_team(self, name, creator_id) -> BTeam:
        team = Team(
            name=name,
            creator_id=creator_id,
            active=True,
        )
        super().store_object(team)
        return BTeam.from_db(team)

    def add_user(self, team_id: int, user_id: int) -> None:
        user_team = UserTeam(team_id=team_id, user_id=user_id)
        super().store_object(user_team)

    def remove_user(self, team_id, user_id) -> None:
        user_team = (
            self.get_session()
            .query(UserTeam)
            .filter(UserTeam.team_id == team_id, UserTeam.user_id == user_id)
            .first()
        )
        self.get_session().delete(user_team)

    def get_by_project_id(self, project_id):

        project = (
            self.get_session()
            .query(Project)
            .filter(Project.id == project_id)
            .filter(Project.active == True)
            .first()
        )
        if project:
            return project.team_id
        return None

    def update_team_name(self, team_id: int, new_name: str):
        """Update a team's name in the database."""
        team = Team.query.filter_by(id=team_id, active=True).first()
        if not team:
            return False

        team.name = new_name
        return team

    def get_team_by_name(self, name):
        return (
            self.get_session()
            .query(Team)
            .filter(Team.name == name)
            .filter(Team.active == True)
            .first()
        )

    def delete_team(self, team_id):
        team = (
            self.get_session()
            .query(Team)
            .filter(Team.id == team_id)
            .filter(Team.active == True)
            .first()
        )
        if not team:
            return False

        team.active = False
        return True
