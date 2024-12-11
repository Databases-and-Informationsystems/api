from collections import namedtuple

from app.repositories.document_repository import DocumentRepository
from app.services.project_service import ProjectService
from tests.test_routes import BaseTestCase
from unittest.mock import patch
import json
from app.services.document_service import DocumentService, document_service
from app.services.user_service import UserService
from app.services.schema_service import SchemaService
from app.db import db


class DocumentsFetchByUserTestCase(BaseTestCase):
    service: DocumentService

    def setUp(self):
        super().setUp()
        self.service = document_service

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(DocumentRepository, "get_documents_by_user")
    def test_get_documents_by_user_valid(
        self,
        get_documents_by_user_mock,
        check_authentication_mock,
    ):

        check_authentication_mock.return_value = 1
        mocked_return = namedtuple(
            "tuple",
            [
                "content",
                "document_edit_id",
                "document_edit_state",
                "id",
                "name",
                "project_id",
                "project_name",
                "team_id",
                "team_name",
                "schema_id",
            ],
        )
        get_documents_by_user_mock.return_value = [
            mocked_return(
                "Doc1",
                1,
                "MENTIONS",
                1,
                "Doc Text1 bla1 bla2 bla3",
                1,
                "Project1",
                1,
                "Team1",
                1,
            )
        ]

        response = self.client.get(
            "/api/documents/",
            headers={"Content-Type": "application/json"},
        )

        # Assert the response is 200 for valid call
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            response.json,
            [
                {
                    "content": "Doc1",
                    "document_edit_id": 1,
                    "document_edit_state": "MENTIONS",
                    "id": 1,
                    "name": "Doc Text1 bla1 bla2 bla3",
                    "project_id": 1,
                    "project_name": "Project1",
                    "team_id": 1,
                    "team_name": "Team1",
                    "schema_id": 1,
                }
            ],
        )
