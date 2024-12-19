import unittest
from unittest.mock import patch, Mock
from werkzeug.exceptions import NotFound, Conflict
from app.models import Mention

from app.repositories.mention_repository import MentionRepository
from app.services.document_edit_service import DocumentEditService
from app.services.mention_services import MentionService, mention_service
from app.services.token_mention_service import TokenMentionService
from app.services.user_service import UserService
from tests.test_routes import BaseTestCase


class TestMentionResource(BaseTestCase):
    service: MentionService

    def setUp(self):
        super().setUp()
        self.service = mention_service

    @patch.object(MentionRepository, "create_mention")
    @patch.object(TokenMentionService, "get_token_mention")
    @patch.object(DocumentEditService, "get_user_id")
    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(MentionRepository, "get_mentions_by_document_edit")
    def test_create_mentions_success(
        self,
        mock_get_mentions_by_document_edit,
        mock_get_logged_in_user_id,
        mock_get_user_id,
        mock_get_token_mention,
        mock_create_mention,
    ):

        # Mock input data
        mock_input_data = {
            "tag": "string",
            "document_edit_id": 123,
            "token_ids": [],
        }

        # Mock services
        mock_get_mentions_by_document_edit.return_value = []
        mock_get_logged_in_user_id.return_value = 1
        mock_get_user_id.return_value = 1  # Same user
        mock_get_token_mention.return_value = []  # No duplicates
        mock_create_mention.return_value = {
            "id": 1,
            "document_edit_id": 123,
            "tag": "sample_tag",
            "entity_id": 789,
        }, 200  # Created mention

        # Call the function
        response, status_code = self.service.create_mentions(mock_input_data)

        # Assertions
        self.assertEqual(status_code, 200)
        self.assertEqual(response["id"], 1)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(DocumentEditService, "get_user_id")
    def test_create_mentions_not_authorized(self, get_user_id, get_logged_in_user_id):
        # Mock input data
        mock_input_data = {
            "tag": "string",
            "document_edit_id": 123,
            "token_ids": [1, 2, 3],
        }

        # Mock services
        get_logged_in_user_id.return_value = 1
        get_user_id.return_value = 2  # Different user

        # Test and assert NotFound exception
        with self.assertRaises(NotFound):
            self.service.create_mentions(mock_input_data)

        # Verify methods were called
        get_logged_in_user_id.assert_called_once()
        get_user_id.assert_called_once_with(123)

    @patch.object(UserService, "get_logged_in_user_id")
    @patch.object(DocumentEditService, "get_user_id")
    @patch.object(TokenMentionService, "get_token_mention")
    @patch.object(MentionRepository, "get_mentions_by_document_edit")
    def test_create_mentions_duplicate_tokens(
        self,
        get_mentions_by_document_edit,
        get_token_mention,
        get_user_id,
        get_logged_in_user_id,
    ):
        # Mock input data
        mock_input_data = {
            "tag": "string",
            "document_edit_id": 123,
            "token_ids": [1, 2, 3],
        }

        # Mock services
        get_logged_in_user_id.return_value = 1
        get_user_id.return_value = 1  # Simulate same user
        get_token_mention.side_effect = ["exists", "duplicate"]

        mock_mention_1 = Mock()
        mock_mention_1.id = 2
        mock_mention_1.document_edit_id = 123
        mock_mention_1.tag = "sample_tag"
        mock_mention_1.entity_id = 789

        mock_mention_2 = Mock()
        mock_mention_2.id = 4
        mock_mention_2.document_edit_id = 1234
        mock_mention_2.tag = "sample_tag"
        mock_mention_2.entity_id = 789

        get_mentions_by_document_edit.return_value = [mock_mention_1, mock_mention_2]

        with self.assertRaises(Conflict):
            self.service.create_mentions(mock_input_data)

        # Verify methods were called
        get_logged_in_user_id.assert_called_once()
        get_user_id.assert_called_once_with(123)
        get_token_mention.assert_any_call([1, 2, 3], [2, 4])


if __name__ == "__main__":
    unittest.main()
