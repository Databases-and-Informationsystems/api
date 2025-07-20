import requests
from flask_restx import Namespace
from werkzeug.exceptions import NotFound, InternalServerError
from flask import request, current_app

from app.file_logger import logger
from app.services.document_service import document_service, DocumentService
from app.dtos import (
    document_output_dto,
    document_create_dto,
    document_list_create_dto,
    document_list_dto,
    document_delete_output_dto,
    heatmap_output_list_dto,
    jaccard_output_dto,
    document_state_update_dto,
    scope_output_dto,
)
from app.routes.base_routes import AuthorizedBaseRoute

ns = Namespace("documents", description="Document related operations")


class DocumentBaseRoute(AuthorizedBaseRoute):
    service: DocumentService = document_service


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentRoutes(DocumentBaseRoute):

    @ns.marshal_with(document_list_dto)
    def get(self):
        """
        Fetch all documents the user has access to.
        Documents also contain list of users which have annotated this document.
        """
        user_id = self.user_service.get_logged_in_user_id()

        response = self.service.get_documents_by_user(user_id)
        return response

    @ns.doc(description="Upload a document to a specific project.")
    @ns.expect(document_create_dto)
    @ns.response(404, "Data not found.")
    @ns.marshal_with(
        document_output_dto,
        description="Document uploaded successfully.",
    )
    def post(self):
        """
        Endpoint for uploading a document to a project.
        """
        data = request.json

        project_id = data.get("project_id")
        file_name = data.get("file_name")
        file_content = data.get("file_content")

        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        # Upload document via service
        document_details = self.service.upload_document(
            user_id,
            project_id=project_id,
            file_name=file_name,
            file_content=file_content,
        )
        return document_details


@ns.route("/list")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentListRoutes(DocumentBaseRoute):

    @ns.expect([document_list_create_dto])
    @ns.response(404, "Data not found.")
    @ns.marshal_with(
        document_output_dto,
        as_list=True,
        description="Document uploaded successfully.",
    )
    @ns.doc(
        params={
            "project_id": {
                "description": "Target project of the documents. (Defines the target schema)",
                "required": True,
            },
        }
    )
    def post(self):
        """
        Endpoint for uploading a list of documents to a project.
        """
        documents = request.json

        project_id = int(request.args.get("project_id"))
        self.verify_positive_integer(project_id)

        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        # Upload document via service
        return [
            self.service.upload_document(
                user_id,
                project_id=project_id,
                file_name=document["file_name"],
                file_content=document["file_content"],
            )
            for document in documents
        ]


@ns.route("/project/<int:project_id>")
@ns.doc(params={"project_id": "A Project ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentProjectRoutes(DocumentBaseRoute):

    @ns.marshal_with(document_list_dto)
    def get(self, project_id):
        """
        Fetch all documents of a project the user has access to.
        Documents also contain list of users which have annotated this document.
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        response = self.service.get_documents_by_project(user_id, project_id)
        return response


@ns.route("/<int:document_id>")
@ns.doc(params={"document_id": "Document ID to soft-delete"})
@ns.response(404, "Document not found")
@ns.response(200, "Document set to inactive successfully")
class DocumentDeletionResource(DocumentBaseRoute):

    @ns.marshal_with(document_delete_output_dto)
    @ns.doc(description="Soft-delete a Document by setting 'active' to False")
    def delete(self, document_id):
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)

        response = self.service.soft_delete_document(document_id)
        return response


@ns.route("/<int:document_id>/heatmap")
@ns.doc(params={"document_id": "A Document ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditsSenderResource(DocumentBaseRoute):

    @ns.marshal_with(heatmap_output_list_dto)
    @ns.doc(
        description="Send all DocumentEdit data for a specific Document ID to an external service"
    )
    def get(self, document_id):
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)

        document_edits = self.service.get_all_document_edits_with_user_by_document(
            document_id
        )
        if not document_edits:
            raise NotFound(f"No DocumentEdits found for Document ID {document_id}")

        document = self.service.get_document_by_id(document_id, user_id)

        transformed_edits = self.service.get_all_structured_document_edits_by_document(
            document_id
        )

        external_endpoint = current_app.config.get("DIFFERENCE_CALC_URL") + "/heatmap"

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.post(
            external_endpoint, json=transformed_edits, headers=headers
        )

        if response.status_code != 200:
            raise InternalServerError("Heatmap calculation failed: " + response.text)

        return {
            "items": response.json(),
            "document": {
                "id": document_id,
                "name": document["name"],
            },
            "document_edits": document_edits,
        }


@ns.route("/<int:document_id>/jaccard-index")
@ns.doc(params={"document_id": "A Document ID"})
@ns.response(400, "Invalid input")
@ns.response(404, "Document not found")
class JaccardIndexResource(DocumentBaseRoute):

    @ns.marshal_with(jaccard_output_dto)
    @ns.doc(
        description="Send all DocumentEdit data for a specific Document ID to an external service"
    )
    def get(self, document_id):
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)

        document = self.service.get_document_by_id(document_id, user_id)
        if not document:
            raise NotFound(f"Document with ID {document_id} not found")

        document_edits = self.service.get_all_document_edits_with_user_by_document(
            document_id
        )
        if not document_edits:
            raise NotFound(f"No DocumentEdits found for Document ID {document_id}")

        transformed_edits = self.service.get_all_structured_document_edits_by_document(
            document_id
        )

        external_endpoint = (
            current_app.config.get("DIFFERENCE_CALC_URL") + "/jaccard-index"
        )
        headers = {"accept": "application/json", "Content-Type": "application/json"}

        response = requests.post(
            external_endpoint, json=transformed_edits, headers=headers
        )
        if response.status_code != 200:
            raise InternalServerError(
                "Jaccard Index calculation failed: " + response.text
            )

        return {
            "document": {
                "id": document_id,
                "name": document["name"],
            },
            "document_edits": document_edits,
            "result": response.json(),
        }


@ns.response(403, "Authorization required")
@ns.route("/<int:document_id>/state")
@ns.doc(params={"document_id": "A Document ID"})
class DocumentStateResource(DocumentBaseRoute):

    @ns.expect(document_state_update_dto)
    @ns.marshal_with(document_output_dto)
    def put(self, document_id):
        """
        Update the state of a document.
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)

        data = request.get_json()
        new_state_id = data.get("state_id")

        updated_document = self.service.change_document_state(
            document_id, new_state_id, user_id
        )

        return updated_document


@ns.route("/interpretations/<int:document_id>")
@ns.doc(params={"document_edit_id": "A Document ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeInterpretationResource(DocumentBaseRoute):

    @ns.marshal_with(scope_output_dto, as_list=True)
    @ns.doc(
        params={
            "model": {
                "description": "Recommendation Model that should be used.",
                "required": False,
            },
            "num_interpretations": {
                "description": "How many interpretations should be generated. Maximum: 10. Default: 4",
                "required": False,
            },
            "pass_interpretations": {
                "description": "Shall interpretations be passed to the model? Default: False",
                "required": False,
            },
            "temperature": {
                "description": f"Temperature of the model",
                "required": False,
            },
            "with_text": {
                "description": f"Include the text in the prompt (only tokens otherwise)? (default: false)",
                "required": False,
            },
            "bottom_up": {
                "description": f"First generate leafs and afterwards scope tree? (default: false)",
                "required": False,
            },
            "only_text": {
                "description": f"Only pass text instead of tokens to the llm? (default: false)",
                "required": False,
            },
        }
    )
    def post(self, document_id):
        """
        Generate recommendations for scopes of a document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)
        logger.info(request.args)
        logger.info(f"document_id: {document_id}")
        model = request.args.get("model")
        num_interpretations = request.args.get("num_interpretations")
        if num_interpretations:
            self.verify_positive_integer(num_interpretations)
        else:
            num_interpretations = 2
        return self.service.get_scope_interpretations(
            user_id, document_id, model, int(num_interpretations), request.args
        )


@ns.route("/interpretations/branches/<int:document_id>")
@ns.doc(params={"document_edit_id": "A Document ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class ScopeInterpretationBranchesResource(DocumentBaseRoute):

    @ns.marshal_with(scope_output_dto, as_list=True)
    @ns.doc(
        params={
            "model": {
                "description": "Recommendation Model that should be used.",
                "required": False,
            },
            "num_interpretations": {
                "description": "How many interpretations should be generated. Maximum: 10. Default: 4",
                "required": False,
            },
            "pass_interpretations": {
                "description": "Shall interpretations be passed to the model? Default: False",
                "required": False,
            },
            "temperature": {
                "description": f"Temperature of the model",
                "required": False,
            },
            "with_text": {
                "description": f"Include the text in the prompt (only tokens otherwise)? (default: false)",
                "required": False,
            },
            "only_text": {
                "description": f"Only pass text instead of tokens to the llm? (default: false)",
                "required": False,
            },
        }
    )
    def post(self, document_id):
        """
        Generate recommendations for scopes of a document edit
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_document_accessible(user_id, document_id)
        logger.info(request.args)
        logger.info(f"document_id: {document_id}")
        model = request.args.get("model")
        num_interpretations = request.args.get("num_interpretations")
        document_edit_leafs_ids = request.args.get("leafs_id").split(",")

        if num_interpretations:
            self.verify_positive_integer(num_interpretations)
        else:
            num_interpretations = 2
        return self.service.get_scope_interpretations_branches(
            user_id,
            document_id,
            model,
            int(num_interpretations),
            request.args,
            document_edit_leafs_ids,
        )
