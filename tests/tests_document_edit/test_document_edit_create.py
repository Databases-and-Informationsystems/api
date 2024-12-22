from collections import namedtuple

from werkzeug.exceptions import BadRequest

from app.repositories.document_edit_repository import DocumentEditRepository
from app.services.document_edit_service import (
    DocumentEditService,
    document_edit_service,
)
from app.services.document_recommendation_service import DocumentRecommendationService
from app.services.document_service import DocumentService
from tests.test_routes import BaseTestCase
from unittest.mock import patch
import json
from app.services.user_service import UserService
from app.db import db


class DocumentEditCreateTestCases(BaseTestCase):
    service: DocumentEditService

    def setUp(self):
        super().setUp()
        self.service = document_edit_service

    @patch.object(DocumentEditService, "create_document_edit")
    def test_create_document_edit_endpoint(self, create_document_edit_mock):
        payload = json.dumps({"document_id": 7})

        create_document_edit_mock.return_value = ""
        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(200, response.status_code)

    @patch.object(DocumentEditService, "create_document_edit")
    def test_create_document_edit_endpoint_wrong_param(self, create_document_edit_mock):
        payload = json.dumps({"name": "document-Name"})

        create_document_edit_mock.return_value = ""
        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(DocumentService, "get_document_by_id")
    @patch.object(DocumentEditService, "get_document_edit_by_document")
    def test_create_document_edit_service_no_access_to_document(
        self,
        get_document_edit_mock,
        get_document_mock,
        check_team_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"document_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.side_effect = BadRequest("You have to be in a team")
        get_document_edit_mock.return_value = None

        mocked_return_get_document = namedtuple(
            "tuple",
            [
                "team_id",
                "document_recommendation_id",
                "schema_id",
            ],
        )
        get_document_mock.return_value = mocked_return_get_document(1, 1, 1)
        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(DocumentEditService, "get_document_edit_by_document")
    @patch.object(db.session, "add")
    @patch.object(db.session, "commit")
    def test_create_document_edit_service_already_exists(
        self,
        db_mock_commit,
        db_mock_add,
        get_document_edit_mock,
        check_team_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"document_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.return_value = ""
        get_document_edit_mock.return_value = {"doc_edit": "object"}

        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        db_mock_add.assert_not_called()
        db_mock_commit.assert_not_called()
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(DocumentService, "get_document_by_id")
    @patch.object(DocumentEditService, "get_document_edit_by_document")
    @patch.object(db.session, "add")
    @patch.object(db.session, "commit")
    def test_create_document_edit_service_document_invalid(
        self,
        db_mock_commit,
        db_mock_add,
        get_document_edit_mock,
        get_document_mock,
        check_team_mock,
        check_auth_mock,
    ):
        payload = json.dumps({"document_id": 7})

        check_auth_mock.return_value = 1
        check_team_mock.return_value = ""
        get_document_edit_mock.return_value = {"doc_edit": "object"}
        get_document_mock.return_value = None

        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        db_mock_add.assert_not_called()
        db_mock_commit.assert_not_called()
        self.assertEqual(400, response.status_code)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(UserService, "check_user_in_team")
    @patch.object(DocumentService, "get_document_by_id")
    @patch.object(DocumentEditService, "get_document_edit_by_document")
    @patch.object(DocumentEditRepository, "create_document_edit")
    @patch.object(DocumentRecommendationService, "create_document_recommendation")
    @patch.object(DocumentRecommendationService, "copy_document_recommendations")
    def test_create_document_edit_service_valid(
        self,
        copy_recommendations_mock,
        create_recommendations_mock,
        create_edit_mock,
        get_document_edit_mock,
        get_document_mock,
        check_team_mock,
        check_auth_mock,
    ):
        doc_id = 7
        payload = json.dumps({"document_id": doc_id})

        mocked_return_get_document = namedtuple(
            "tuple",
            [
                "team_id",
                "document_recommendation_id",
                "schema_id",
            ],
        )
        mocked_return_create_edit = namedtuple(
            "tuple",
            ["id", "document_id", "schema_id"],
        )
        mocked_return_create_recommendation = namedtuple(
            "tuple",
            [
                "id",
            ],
        )

        check_auth_mock.return_value = 1

        get_document_mock.return_value = mocked_return_get_document(
            1,
            1,
            1,
        )

        check_team_mock.return_value = ""

        get_document_edit_mock.return_value = None
        copy_recommendations_mock.return_value = None
        create_recommendations_mock.return_value = mocked_return_create_recommendation(
            1,
        )
        create_edit_mock.return_value = mocked_return_create_edit(
            1, document_id=doc_id, schema_id=1
        )

        response = self.client.post(
            "/api/document_edits/",
            headers={"Content-Type": "application/json"},
            data=payload,
        )

        create_edit_mock.assert_called_once()
        create_recommendations_mock.assert_called_once()
        copy_recommendations_mock.assert_called_once()
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json.get("document_id"), 7)
