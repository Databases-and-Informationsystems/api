from collections import namedtuple

from werkzeug.exceptions import BadRequest

from tests.test_routes import BaseTestCase
from unittest.mock import patch
import json
from app.services.team_service import TeamService, team_service
from app.services.user_service import UserService


class TeamAddUserTestCases(BaseTestCase):
    service: TeamService

    def setUp(self):
        super().setUp()
        self.service = team_service

    @patch.object(TeamService, "add_user_to_team")
    def test_team_add_user_endpoint(self, add_user_team_mock):
        payload = json.dumps({"user_mail": "mail@mail.de", "team_id": 7})

        add_user_team_mock.return_value = ""
        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(200, response.status_code)

    @patch.object(TeamService, "add_user_to_team")
    def test_team_add_user_service_wrong_param(self, create_team_mock):
        payload = json.dumps({"team_id": 7, "username": "user-Name"})

        create_team_mock.return_value = ""
        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "get_user_by_mail")
    def test_team_add_user_service_user_not_exists(
        self, get_user_mock, check_auth_mock
    ):
        payload = json.dumps({"user_mail": "mail@mail.de", "team_id": 7})

        check_auth_mock.return_value = 1
        get_user_mock.return_value = None

        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.json.get("message"), "User not found")

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "get_user_by_mail")
    @patch.object(UserService, "check_user_in_team")
    def test_team_add_user_service_user_already_member(
        self,
        check_user_team_mock,
        get_user_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"user_mail": "mail@mail.de", "team_id": 7})

        check_auth_mock.return_value = 1

        check_user_team_mock.return_value = None
        mocked_return_get_user = namedtuple(
            "tuple",
            ["id", "username", "email"],
        )

        get_user_mock.return_value = mocked_return_get_user(1, "user-Name", "<EMAIL>")

        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        self.assertEqual(409, response.status_code)
        self.assertEqual(
            response.json.get("message"), "User is already part of the team"
        )

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "get_user_by_mail")
    @patch.object(UserService, "check_user_in_team")
    def test_team_add_user_service_user_already_member(
        self,
        check_user_team_mock,
        get_user_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"user_mail": "mail@mail.de", "team_id": 7})

        check_auth_mock.return_value = 1

        check_user_team_mock.return_value = None
        mocked_return_get_user = namedtuple(
            "tuple",
            ["id", "username", "email"],
        )

        get_user_mock.return_value = mocked_return_get_user(1, "user-Name", "<EMAIL>")

        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        self.assertEqual(409, response.status_code)
        self.assertEqual(
            response.json.get("message"), "User is already part of the team"
        )

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "get_user_by_mail")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(TeamService, "add_user")
    def test_team_add_user_service_valid(
        self,
        add_user_team_mock,
        check_user_team_mock,
        get_user_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"user_mail": "mail@mail.de", "team_id": 7})

        check_auth_mock.return_value = 1

        # First call: logged-in user is part of the team
        # Second call: new member is not already part of the team
        check_user_team_mock.side_effect = [None, BadRequest()]

        mocked_return_get_user = namedtuple(
            "tuple",
            ["id", "username", "email"],
        )
        get_user_mock.return_value = mocked_return_get_user(1, "user-Name", "<EMAIL>")

        add_user_team_mock.return_value = None

        response = self.client.post(
            "/api/teams/members",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json.get("username"), "user-Name")
