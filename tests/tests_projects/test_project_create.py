from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound

from tests.test_routes import BaseTestCase
from unittest.mock import patch
import json
from app.services.project_service import ProjectService, project_service
from app.services.user_service import UserService
from app.services.schema_service import SchemaService
from app.db import db


class ProjectCreateTestCases(BaseTestCase):
    service: ProjectService

    def setUp(self):
        super().setUp()
        self.service = project_service

    @patch.object(ProjectService, "create_project")
    def test_create_project_endpoint(self, create_project_mock):
        payload = json.dumps({"name": "Project-Name", "team_id": 2, "schema_id": 7})

        create_project_mock.return_value = "", 200
        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(200, response.status_code)

    @patch.object(ProjectService, "create_project")
    def test_create_project_service_wrong_param(self, create_project_mock):
        payload = json.dumps({"name": "Project-Name", "schema_id": 7})

        create_project_mock.return_value = "", 200
        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    def test_create_project_service_invalid_user_auth(self, check_auth_mock):
        payload = json.dumps({"name": "Project-Name", "team_id": 2, "schema_id": 7})

        check_auth_mock.side_effect = Forbidden("You need to be logged in")

        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(403, response.status_code)
        self.assertEqual(response.json.get("message"), "You need to be logged in")

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    def test_create_project_service_no_team(self, check_team_mock, check_auth_mock):
        payload = json.dumps({"name": "Project-Name", "team_id": 2, "schema_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.side_effect = BadRequest("You have to be in a team")

        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json.get("message"), "You have to be in a team")

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(SchemaService, "check_schema_exists")
    @patch.object(db.session, "add")
    def test_create_project_service_no_schema(
        self, db_mock, check_schema_mock, check_team_mock, check_auth_mock
    ):
        payload = json.dumps({"name": "Project-Name", "team_id": 2, "schema_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.return_value = "", 200
        check_schema_mock.side_effect = NotFound("Schema not found")
        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(404, response.status_code)
        db_mock.assert_not_called()

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(SchemaService, "check_schema_exists")
    @patch.object(db.session, "add")
    @patch.object(db.session, "commit")
    def test_create_project_service_valid(
        self,
        db_mock_commit,
        db_mock_add,
        check_schema_mock,
        check_team_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"name": "Project-Name", "team_id": 2, "schema_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.return_value = "", 200
        check_schema_mock.return_value = "", 200

        response = self.client.post(
            "/api/projects/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        db_mock_add.assert_called_once()
        db_mock_commit.assert_called_once()
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json.get("name"), "Project-Name")
