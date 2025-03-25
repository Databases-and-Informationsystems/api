import json
import typing
from datetime import timedelta
from app.config import Config
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized, NotFound
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity

from app.models.buisness_models import BUser
from app.repositories.user_repository import UserRepository
from app.services.document_edit_service import (
    DocumentEditService,
    document_edit_service,
)
from app.services.schema_service import SchemaService, schema_service


def create_jwt_token(user: BUser) -> str:
    expires_delta = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    return create_access_token(
        identity=json.dumps(user.as_jwt_content()), expires_delta=expires_delta
    )


class UserService:
    __user_repository: UserRepository
    __document_edit_service: DocumentEditService
    __schema_service: SchemaService

    def __init__(
        self,
        user_repository: UserRepository,
        document_edit_service: DocumentEditService,
        schema_service: SchemaService,
    ):
        self.__user_repository = user_repository
        self.__document_edit_service = document_edit_service
        self.__schema_service = schema_service

    def is_user_in_team(self, user_id: int, team_id: int) -> bool:
        return self.__user_repository.is_user_in_team(user_id, team_id)

    def check_user_in_team(self, user_id, team_id):
        """
        Checks if user is part of the team

        :param user_id: User ID
        :param team_id: Team ID
        :raises Forbidden: If user does not belong to team

        """
        if self.__user_repository.is_user_in_team(user_id, team_id) is None:
            raise Forbidden("You are not part of this team")

    # TODO should be in session Service
    def get_user(self) -> BUser:
        """
        Get the full JSON object of the currently logged-in user.

        :return: JSON object containing user identity information.
        :raises Unauthorized: If no user is logged in.
        """
        try:
            identity = get_jwt_identity()
            user_data = json.loads(identity)
            user = BUser.from_json(user_data)
            return user
        except Exception as e:
            raise Unauthorized(str(e))

    # TODO should be in session Service
    def get_user_id(self) -> int:
        """
        Get the ID of the currently logged-in user from the JWT identity.

        :return: User ID
        :raises Unauthorized: If no user is logged in.
        """
        user = self.get_user()
        return user.id

    def get_user_by_email(self, mail) -> typing.Optional[BUser]:
        return self.__user_repository.get_user_by_email(mail)

    def get_user_by_username(self, username):
        return self.__user_repository.get_user_by_username(username)

    def create_user(self, user: BUser) -> BUser:
        return self.__user_repository.create_user(user)

    def signup(self, user: BUser) -> typing.Tuple[BUser, str]:
        if self.get_user_by_username(user.username):
            raise BadRequest("Username already exists")
        if self.get_user_by_email(user.email):
            raise BadRequest("Email already exists")

        # TODO use proper password safety validation
        if not user.password or len(user.password) < 6:  # Example validation
            raise BadRequest("Password must be at least 6 characters long")

        user.password = generate_password_hash(user.password, method="pbkdf2:sha256")

        user = (
            self.create_user(user)
            .with_document_edits(self.__document_edit_service.get_ids_by_user(user.id))
            .with_schemas(self.__schema_service.get_ids_by_user(user.id))
        )
        token = create_jwt_token(user)
        return user, token

    def check_user_document_accessible(self, user_id, document_id):
        """
        Checks if user has access to document

        :param user_id: User ID
        :param document_id: Document ID
        :raises Forbidden: If user has no access to document
        """
        document = self.__user_repository.check_user_document_accessible(
            user_id, document_id
        )
        if document is None:
            raise Forbidden("You cannot access this document")

    def check_user_document_edit_accessible(self, user_id, document_edit_id):
        """
        Checks if user has access to document edit

        :param user_id: User ID
        :param document_edit_id: DocumentEdit ID
        :raises Forbidden: If user has no access to document edit
        """
        document_edit_user_id = self.__user_repository.get_user_by_document_edit_id(
            document_edit_id
        )

        if int(user_id) != int(document_edit_user_id):
            raise Forbidden("You cannot access this document edit")

    def check_user_schema_accessible(self, user_id, schema_id):
        """
        Checks if user has access to schema

        :param user_id: User ID
        :param schema_id: Schema ID
        :raises Forbidden: If user has no access to schema
        """
        if (
            self.__user_repository.check_user_schema_accessible(user_id, schema_id)
            is None
        ):
            raise Forbidden("You cannot access this schema")

    def check_user_project_accessible(self, user_id, project_id):
        """
        Checks if user has access to project

        :param user_id: User ID
        :param project_id: Project ID
        :raises Forbidden: If user has no access to project
        """
        if (
            self.__user_repository.check_user_project_accessible(user_id, project_id)
            is None
        ):
            raise Forbidden("You cannot access this project")

    def check_user_entity_accessible(self, user_id, entity_id):
        """
        Checks if user has access to entity

        :param user_id: User ID
        :param entity_id: Entity ID
        :raises Forbidden: If user has no access to entity
        """
        if (
            self.__user_repository.check_user_entity_accessible(user_id, entity_id)
            is None
        ):
            raise Forbidden("You cannot access this entity")

    def check_user_relation_accessible(self, user_id, relation_id):
        """
        Checks if user has access to relation

        :param user_id: User ID
        :param relation_id: Relation ID
        :raises Forbidden: If user has no access to relation
        """
        if (
            self.__user_repository.check_user_relation_accessible(user_id, relation_id)
            is None
        ):
            raise Forbidden("You cannot access this relation")

    def check_user_mention_accessible(self, user_id, mention_id):
        """
        Checks if user has access to mention

        :param user_id: User ID
        :param mention_id: Mention ID
        :raises Forbidden: If user has no access to mention
        """
        if (
            self.__user_repository.check_user_mention_accessible(user_id, mention_id)
            is None
        ):
            raise Forbidden("You cannot access this mention")

    def login(self, email, password) -> typing.Tuple[BUser, str]:
        user: BUser = self.get_user_by_email(email)
        if not user:
            raise Unauthorized("Invalid email or password")

        if not check_password_hash(user.password, password):
            raise Unauthorized("Invalid email or password")

        user.with_document_edits(
            self.__document_edit_service.get_ids_by_user(user.id)
        ).with_schemas(self.__schema_service.get_ids_by_user(user.id))

        token = create_jwt_token(user)
        return user, token

    def update_user_data(self, user_id, username=None, email=None, password=None):
        """
        Update user information by calling the repository.

        :param user_id: ID of the user
        :param username: New username (optional).
        :param email: New email (optional).
        :param password: New password (optional).
        :raises BadRequest: If no fields to update are provided.
        :raises NotFound: If the user is not found.
        :return: Updated user data.
        """
        if not any([username, email, password]):
            raise BadRequest("No fields to update provided.")

        if username and self.get_user_by_username(username):
            raise BadRequest("Username already exists")
        if email and self.get_user_by_email(email):
            raise BadRequest("Email already exists")

        updated_user = self.__user_repository.update_user_data(
            user_id=user_id,
            username=username,
            email=email,
            password=password,
        )
        return {
            "id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
        }

    def get_user_by_id(self, user_id):
        """
        Fetch user by its ID

        :param user_id: User ID
        :return: user_output_dto
        :raises NotFound: If the user does not exist
        """
        user = self.__user_repository.get_user_by_id(user_id)
        if user is None:
            return NotFound("User not found")
        return {"id": user.id, "username": user.username, "email": user.email}


user_service = UserService(
    user_repository=UserRepository(),
    document_edit_service=document_edit_service,
    schema_service=schema_service,
)
