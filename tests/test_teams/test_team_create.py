from collections import namedtuple

from sqlalchemy.exc import IntegrityError

from app.repositories.team_repository import TeamRepository
from tests.test_routes import BaseTestCase
from unittest.mock import patch, MagicMock
import json
from app.services.team_service import TeamService, team_service
from app.services.user_service import UserService


class TeamCreateTestCases(BaseTestCase):
    service: TeamService

    def setUp(self):
        super().setUp()
        self.service = team_service

    @patch.object(TeamService, "create_team")
    def test_create_team_endpoint(self, create_team_mock):
        payload = json.dumps({"name": "team-Name"})

        create_team_mock.return_value = ""
        response = self.client.post(
            "/api/teams/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(200, response.status_code)

    @patch.object(TeamService, "create_team")
    def test_create_team_service_wrong_param(self, create_team_mock):
        payload = json.dumps({"id": 7})

        create_team_mock.return_value = ""
        response = self.client.post(
            "/api/teams/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(TeamRepository, "create_team")
    def test_create_team_service_name_already_exists(
        self, create_team_mock, check_auth_mock
    ):
        payload = json.dumps({"name": "team-Name"})

        check_auth_mock.return_value = 1
        create_team_mock.side_effect = IntegrityError("Mock", "Mock", MagicMock())

        response = self.client.post(
            "/api/teams/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json.get("message"), "Teamname already exists")

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(TeamRepository, "create_team")
    @patch.object(TeamService, "add_user")
    def test_create_team_service_valid(
        self,
        add_user_mock,
        create_team_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"name": "team-Name"})

        check_auth_mock.return_value = 1

        mocked_return_create_team = namedtuple(
            "tuple",
            ["id", "name", "creator_id"],
        )

        create_team_mock.return_value = mocked_return_create_team(1, "team-Name", 1)
        add_user_mock.return_value = None
        response = self.client.post(
            "/api/teams/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        create_team_mock.assert_called()
        add_user_mock.assert_called_once()
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json.get("name"), "team-Name")
