from werkzeug.exceptions import NotFound
from app.repositories.token_repository import TokenRepository
from tests.test_routes import BaseTestCase
from unittest.mock import patch
from app.services.token_service import TokenService, token_service
import requests


class TokenizationTestCases(BaseTestCase):
    service: TokenService

    def setUp(self):
        super().setUp()
        self.service = token_service

    @patch.object(requests, "post")
    @patch.object(TokenRepository, "create_token")
    def test_tokenization_service_failed(
        self, create_token_mock, pipeline_tokenize_mock
    ):
        pipeline_tokenize_mock.return_value.json.return_value = invalid_response
        create_token_mock.return_value = ""
        with self.app.app_context():
            with self.assertRaises(NotFound):
                self.service.tokenize_document(1, "Content of Document")

    @patch.object(requests, "post")
    @patch.object(TokenRepository, "create_token")
    def test_tokenization_service_valid(
        self, create_token_mock, pipeline_tokenize_mock
    ):
        pipeline_tokenize_mock.return_value.json.return_value = valid_response
        create_token_mock.return_value = ""

        pipeline_tokenize_mock.return_value.status_code = 200
        with self.app.app_context():
            res = self.service.tokenize_document(1, "Content of Document")
        self.assertEqual(res[1], 200)
        self.assertEqual(
            res[0],
            [
                {
                    "document_index": 0,
                    "id": None,
                    "pos_tag": "DT",
                    "sentence_index": 0,
                    "text": "The",
                },
                {
                    "document_index": 1,
                    "id": None,
                    "pos_tag": "NNP",
                    "sentence_index": 0,
                    "text": "MSPN",
                },
                {
                    "document_index": 2,
                    "id": None,
                    "pos_tag": "VBZ",
                    "sentence_index": 0,
                    "text": "registers",
                },
            ],
        )


invalid_response = {
    "document": {"tokens": None},
    "entities": None,
    "mentions": None,
    "relations": None,
    "state": None,
}

valid_response = {
    "document": {
        "content": "The MSPN registers.",
        "id": None,
        "name": "Test Document 1",
        "state": None,
        "tokens": [
            {
                "document_index": 0,
                "id": None,
                "pos_tag": "DT",
                "sentence_index": 0,
                "text": "The",
            },
            {
                "document_index": 1,
                "id": None,
                "pos_tag": "NNP",
                "sentence_index": 0,
                "text": "MSPN",
            },
            {
                "document_index": 2,
                "id": None,
                "pos_tag": "VBZ",
                "sentence_index": 0,
                "text": "registers",
            },
        ],
    },
    "entities": None,
    "mentions": None,
    "relations": None,
    "state": None,
}
