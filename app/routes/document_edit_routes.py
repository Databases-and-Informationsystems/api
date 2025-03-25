from flask_restx import Namespace
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.document_edit_service import (
    document_edit_service,
    DocumentEditService,
)
import json
from flask import request, Response
from app.dtos import (
    document_edit_output_dto,
    document_edit_input_dto,
    document_overtake_dto,
    document_edit_output_soft_delete_dto,
    finished_document_edit_output_dto,
    document_edit_model_output_list_dto,
    document_edit_state_input_dto,
    document_edit_schema_output_dto,
    f1_score_dto,
)

ns = Namespace("annotations", description="Document-Annotation related operations")


class DocumentEditBaseRoute(AuthorizedBaseRoute):
    service: DocumentEditService = document_edit_service


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditCreateResource(DocumentEditBaseRoute):

    @ns.marshal_with(document_edit_output_dto)
    @ns.expect(document_edit_input_dto)
    def post(self):
        """
        Create a new document annotation.
        Generates recommendations for mentions and stores them for the newly created annotation.

        [Optional] takes ids and settings of models available inside the schema for mention, entity and relation suggestion.
        If not specified, default models (LLM) and default settings are used.
        """
        data = request.get_json()

        document_id = (data.get("document_id"),)
        user_id = self.user_service.get_user_id()

        self.user_service.check_user_document_accessible(user_id, document_id)

        response = self.service.create_document_edit(
            user_id,
            document_id,
            data.get("model_mention_id"),
            data.get("model_entities_id"),
            data.get("model_relation_id"),
            data.get("model_settings_mention"),
            data.get("model_settings_entities"),
            data.get("model_settings_relation"),
        )
        return response


@ns.route("/overtake")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditOvertakeResource(DocumentEditBaseRoute):

    @ns.doc(description="overtake another user annotation")
    @ns.marshal_with(document_edit_output_dto)
    @ns.expect(document_overtake_dto)
    def post(self):
        data = request.json
        user_id = self.user_service.get_user_id()

        response = self.service.overtake_document_edit(
            user_id, data.get("document_edit_id")
        )
        return response


@ns.route("/<int:document_edit_id>")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditDeleteFetchResource(DocumentEditBaseRoute):

    @ns.marshal_with(document_edit_output_soft_delete_dto)
    @ns.doc(description="Soft-delete a DocumentEdit by setting 'active' to False")
    def delete(self, document_edit_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.soft_delete_document_edit(document_edit_id)
        return response

    @ns.marshal_with(finished_document_edit_output_dto)
    @ns.doc(description="Fetch details of a DocumentEdit by its ID")
    def get(self, document_edit_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.get_document_edit_by_id(document_edit_id, user_id)
        return response.to_json()


@ns.route("/<int:document_edit_id>/model")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditModelResource(DocumentEditBaseRoute):

    @ns.marshal_with(document_edit_model_output_list_dto)
    def get(self, document_edit_id):
        """
        Fetch selected models with associated settings chosen for this annotation.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.get_document_edit_model(document_edit_id)
        return response


@ns.route("/<int:document_edit_id>/step")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditStateResource(DocumentEditBaseRoute):

    @ns.marshal_with(document_edit_output_dto)
    @ns.expect(document_edit_state_input_dto, validate=True)
    def post(self, document_edit_id):
        """
        Set Edit State of a document edit to another step.
        Possible is only the directly following step.

        When proceeding to a suggestion step, new recommendations will be generated.
        If unreviewed recommendations exist, it is forbidden to leave the suggestion step.
        """
        request_data = request.get_json()

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response = self.service.set_edit_state(document_edit_id, request_data["state"])
        return response


@ns.route("/<int:document_edit_id>/download")
@ns.doc(params={"document_edit_id": "A Document Edit ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditResource(DocumentEditBaseRoute):

    @ns.doc(description="Download a DocumentEdit by its ID")
    def get(self, document_edit_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)

        response_data = self.service.get_document_edit_by_id_for_difference_calc(
            document_edit_id
        )
        json_data = json.dumps(response_data, indent=4)

        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=document_edit.json"},
        )


@ns.route("/schema/<int:schema_id>")
@ns.doc(params={"schema_id": "A schema ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditSchemaResource(DocumentEditBaseRoute):

    @ns.marshal_with(document_edit_schema_output_dto, as_list=True)
    def get(self, schema_id):
        """
        Fetch a list of all document edits by schema id.
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_schema_accessible(user_id, schema_id)

        response = self.service.get_document_edits_by_schema(schema_id)
        return response


@ns.route("/<int:document_edit_id>/f1score")
@ns.doc(params={"document_edit_id": "A Document ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class DocumentEditF1Score(DocumentEditBaseRoute):

    @ns.marshal_with(f1_score_dto)
    @ns.doc(description="Get F1 score for document edit")
    def get(self, document_edit_id):
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_document_edit_accessible(user_id, document_edit_id)
        return self.service.get_f1_score(document_edit_id)
