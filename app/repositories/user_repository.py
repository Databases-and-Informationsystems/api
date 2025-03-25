import typing

from sqlalchemy import and_
from werkzeug.exceptions import NotFound
from app.models.db_models import (
    UserTeam,
    DocumentEdit,
    User,
    Team,
    Project,
    Document,
    Schema,
    DocumentRecommendation,
    Entity,
    Relation,
    Mention,
)

from app.models.buisness_models import BUser
from app.repositories.base_repository import BaseRepository
from werkzeug.security import generate_password_hash


class UserRepository(BaseRepository):
    def is_user_in_team(self, user_id, team_id) -> bool:
        return (
            self.get_session()
            .query(UserTeam)
            .join(Team, Team.id == UserTeam.team_id)
            .filter(UserTeam.user_id == user_id, UserTeam.team_id == team_id)
            .filter(Team.active == True)
            .first()
        ) is not None

    def get_user_by_email(self, mail) -> typing.Optional[BUser]:
        user = self.get_session().query(User).filter(User.email == mail).first()
        if user is None:
            return None
        return BUser.from_db(user)

    def get_user_by_document_edit_id(self, document_edit_id) -> int:
        document_edit = (
            self.get_session()
            .query(DocumentEdit)
            .filter(DocumentEdit.id == document_edit_id)
            .filter(DocumentEdit.active == True)
            .first()
        )
        if document_edit is None:
            raise NotFound("Document Edit not found")
        return int(document_edit.user_id)

    def get_user_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def create_user(self, user: BUser) -> BUser:
        new_user = user.to_db()
        self.store_object(new_user)
        return BUser.from_db(new_user)

    def check_user_document_accessible(self, user_id, document_id):
        return (
            self.get_session()
            .query(
                Document,
                Project.schema_id,
                DocumentRecommendation.id.label("document_recommendation_id"),
            )
            .select_from(UserTeam)
            .join(Team, UserTeam.team_id == Team.id)
            .join(Project, Project.team_id == Team.id)
            .join(Document, Document.project_id == Project.id)
            .outerjoin(
                DocumentRecommendation,
                and_(
                    Document.id == DocumentRecommendation.document_id,
                    DocumentRecommendation.document_edit_id is None,
                ),
            )
            .filter((Document.id == document_id) & (UserTeam.user_id == user_id))
            .filter(Document.active == True)
            .first()
        )

    def check_user_schema_accessible(self, user_id, schema_id):
        return (
            self.get_session()
            .query(UserTeam)
            .join(Team, UserTeam.team_id == Team.id)
            .join(Schema, Schema.team_id == Team.id)
            .filter((Schema.id == schema_id) & (UserTeam.user_id == user_id))
            .filter(Schema.active == True)
            .first()
        )

    def check_user_project_accessible(self, user_id, project_id):
        return (
            self.get_session()
            .query(UserTeam)
            .join(Project, Project.team_id == UserTeam.team_id)
            .filter((Project.id == project_id) & (UserTeam.user_id == user_id))
            .first()
        )

    def check_user_entity_accessible(self, user_id, entity_id):
        return (
            self.get_session()
            .query(Entity)
            .join(DocumentEdit, DocumentEdit.id == Entity.document_edit_id)
            .filter(Entity.id == entity_id)
            .filter(DocumentEdit.user_id == user_id)
            .first()
        )

    def check_user_relation_accessible(self, user_id, relation_id):
        return (
            self.get_session()
            .query(Relation)
            .join(DocumentEdit, DocumentEdit.id == Relation.document_edit_id)
            .filter(Relation.id == relation_id)
            .filter(DocumentEdit.user_id == user_id)
            .first()
        )

    def check_user_mention_accessible(self, user_id, mention_id):
        return (
            self.get_session()
            .query(Mention)
            .join(DocumentEdit, DocumentEdit.id == Mention.document_edit_id)
            .filter(Mention.id == mention_id)
            .filter(DocumentEdit.user_id == user_id)
            .first()
        )

    def update_user_data(self, user_id, username=None, email=None, password=None):
        """
        Update user information in the database.

        :param user_id: ID of the user to update.
        :param username: New username (optional).
        :param email: New email (optional).
        :param password: New password, will be hashed before storing (optional).
        :raises NotFound: If the user is not found.
        """
        user = self.get_session().query(User).filter_by(id=user_id).one_or_none()
        if not user:
            raise NotFound(f"User with ID {user_id} not found.")

        if username:
            user.username = username
        if email:
            user.email = email
        if password:
            user.password = generate_password_hash(password)

        return user

    def get_user_by_id(self, user_id):
        return self.get_session().query(User).filter_by(id=user_id).first()
