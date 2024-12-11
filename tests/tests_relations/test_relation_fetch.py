import json
from unittest.mock import patch

from werkzeug.exceptions import NotFound

from app.services.relation_services import RelationService, relation_service
from app.db import db
from tests.test_routes import BaseTestCase


class RelationTestCases(BaseTestCase):
    service: RelationService

    def setUp(self):
        super().setUp()
        self.service = relation_service

    @patch.object(RelationService, "get_relations_by_document_edit")
    def test_get_relations_by_document_edit_valid(self, get_relations_mock):
        # Mocked response for the test
        get_relations_mock.return_value = {
            "relations": [
                {
                    "id": 1,
                    "isDirected": False,
                    "isShownRecommendation": False,
                    "mention_head_id": 1,
                    "mention_tail_id": 2,
                    "tag": "tag",
                },
                {
                    "id": 2,
                    "isDirected": False,
                    "isShownRecommendation": False,
                    "mention_head_id": 1,
                    "mention_tail_id": 2,
                    "tag": "tag",
                },
            ]
        }

        # Sending GET request with the document edit ID
        response = self.client.get("/api/relations/1")

        # Check the response status code and data
        self.assertEqual(200, response.status_code)
        self.assertIn("relations", response.json)
        self.assertEqual(
            response.json.get("relations"),
            [
                {
                    "id": 1,
                    "isDirected": False,
                    "isShownRecommendation": False,
                    "mention_head_id": 1,
                    "mention_tail_id": 2,
                    "tag": "tag",
                },
                {
                    "id": 2,
                    "isDirected": False,
                    "isShownRecommendation": False,
                    "mention_head_id": 1,
                    "mention_tail_id": 2,
                    "tag": "tag",
                },
            ],
        )

    @patch.object(RelationService, "get_relations_by_document_edit")
    def test_get_relations_by_document_edit_not_found(self, get_relations_mock):
        # Mock response for a case where no relations are found
        get_relations_mock.side_effect = NotFound(
            "No relations found for the given document edit."
        )

        # Sending GET request with a document edit ID that doesn't exist
        response = self.client.get("/api/relations/999")

        # Assert the response status code and the returned error message
        self.assertEqual(404, response.status_code)

    @patch.object(RelationService, "get_relations_by_document_edit")
    def test_get_relations_by_document_edit_bad_request(self, get_relations_mock):
        # Mock the service to simulate no service call (validation fails early)
        get_relations_mock.return_value = None

        # Sending GET request with invalid document_edit ID (non-integer)
        response = self.client.get("/api/relations/abc")

        # Assert the response is 404
        self.assertEqual(404, response.status_code)
