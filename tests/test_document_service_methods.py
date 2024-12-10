# tests/test_document_service_methods.py
from unittest import TestCase
from unittest.mock import MagicMock
from app.services.document_service import DocumentService
from werkzeug.exceptions import Forbidden, InternalServerError


class TestDocumentServiceMethods(TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_document_repository = MagicMock()
        self.mock_project_service = MagicMock()
        
        # Initialize DocumentService with mocked repository
        self.service = DocumentService(self.mock_document_repository)

    def test_check_user_permission_success(self):
        """
        Test user permission check when the user is part of the project.
        """
        # Mock data
        user_id = 1
        project_id = 1

        # Configure the project_service mock to return True
        self.mock_project_service.is_user_in_project.return_value = True

        # Call the method (simulate the check)
        result = self.service.upload_document(
            user_id=user_id,
            project_id=project_id,
            document_name="Test Document",
            document_content="Sample content",
            project_service=self.mock_project_service,
        )

        # Assert
        self.mock_project_service.is_user_in_project.assert_called_once_with(user_id, project_id)
        self.assertEqual(result["message"], "Document uploaded successfully")

    def test_check_user_permission_forbidden(self):
        """
        Test user permission check when the user is not part of the project.
        """
        # Mock data
        user_id = 1
        project_id = 1

        # Configure the project_service mock to return False
        self.mock_project_service.is_user_in_project.return_value = False

        # Call the method and assert exception
        with self.assertRaises(Forbidden):
            self.service.upload_document(
                user_id=user_id,
                project_id=project_id,
                document_name="Test Document",
                document_content="Sample content",
                project_service=self.mock_project_service,
            )

        self.mock_project_service.is_user_in_project.assert_called_once_with(user_id, project_id)

    def test_document_data_preparation(self):
        """
        Test document data preparation logic in the service.
        """
        # Mock data
        user_id = 1
        project_id = 1
        document_name = "Test Document"
        document_content = "Sample content"

        # Expected data
        expected_data = {
            "name": document_name,
            "content": document_content,
            "creator_id": user_id,
            "project_id": project_id,
        }

        # Mock project_service to allow upload
        self.mock_project_service.is_user_in_project.return_value = True

        # Call the method (to simulate preparation and saving)
        self.service.upload_document(
            user_id=user_id,
            project_id=project_id,
            document_name=document_name,
            document_content=document_content,
            project_service=self.mock_project_service,
        )

        # Assert that the data was passed to the repository correctly
        self.mock_document_repository.create_document.assert_called_once_with(expected_data)

    def test_document_save_internal_server_error(self):
        """
        Test that an internal server error is raised when document saving fails.
        """
        # Mock data
        user_id = 1
        project_id = 1
        document_name = "Test Document"
        document_content = "Sample content"

        # Configure mocks
        self.mock_project_service.is_user_in_project.return_value = True
        self.mock_document_repository.create_document.side_effect = Exception("Database error")

        # Call the method and assert exception
        with self.assertRaises(InternalServerError):
            self.service.upload_document(
                user_id=user_id,
                project_id=project_id,
                document_name=document_name,
                document_content=document_content,
                project_service=self.mock_project_service,
            )

        self.mock_document_repository.create_document.assert_called_once()
