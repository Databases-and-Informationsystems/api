import requests
from flask import request, current_app
from flask_restx import Namespace
from werkzeug.exceptions import BadRequest

from app.dtos import (
    schema_output_dto,
    schema_output_list_dto,
    schema_input_dto,
    get_recommendation_models_output_dto,
)
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.schema_service import schema_service, SchemaService

ns = Namespace("schemas", description="Schema related operations")


class SchemaBaseRoute(AuthorizedBaseRoute):
    service: SchemaService = schema_service


@ns.route("")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaResource(SchemaBaseRoute):

    @ns.marshal_with(schema_output_list_dto)
    def get(self):
        """
        Fetch all schemas the user has access to
        """
        user_id = self.user_service.get_logged_in_user_id()

        return self.service.get_schemas_by_user(user_id)

    @ns.doc(
        params={
            "team_id": {
                "type": "integer",
                "required": True,
                "description": "Target team of the schema.",
            }
        }
    )
    @ns.marshal_with(schema_output_dto)
    @ns.expect(schema_input_dto)
    def post(self):
        """
        Creates a schema for given team ID
        """
        import_schema = request.get_json()

        team_id = request.args.get("team_id")
        self.verify_positive_integer(team_id)

        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_in_team(user_id, team_id)

        return self.service.create_extended_schema(import_schema, int(team_id))


@ns.route("/<int:schema_id>")
@ns.doc(params={"schema_id": "A Schema ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaQueryResource(SchemaBaseRoute):

    @ns.marshal_with(schema_output_dto)
    def get(self, schema_id):
        """
        Fetch schema by schema ID
        """
        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_schema_accessible(user_id, schema_id)

        response = self.service.get_schema_by_id(schema_id)
        return response


@ns.route("/<int:schema_id>/recommendation")
class ModelRoutes(SchemaBaseRoute):

    @ns.marshal_with(get_recommendation_models_output_dto)
    def get(self, schema_id):
        """
        Fetch recommendation models  of schema with possible settings-
        """

        user_id = self.user_service.get_logged_in_user_id()
        self.user_service.check_user_schema_accessible(user_id, schema_id)

        models = schema_service.get_models_by_schema(schema_id)

        steps = ["mention", "entity", "relation"]
        response = {}
        for step in steps:
            response[step] = []
        headers = {"Content-Type": "application/json"}

        pipeline_response = {}
        for step in steps:
            url = current_app.config.get("PIPELINE_URL") + "/steps/" + step
            step_response = requests.get(url=url, headers=headers)
            if step_response.status_code != 200:
                raise BadRequest("Failed to fetch models: " + step_response.text)
            pipeline_response[step] = step_response.json()

        for model in models:
            model_response = {}
            step = None
            if model["step"]["id"] == 1:
                step = "mention"
            elif model["step"]["id"] == 2:
                step = "entity"
            elif model["step"]["id"] == 3:
                step = "relation"

            for pipeline_model in pipeline_response[step]:
                if model["type"] == pipeline_model["model_type"]:
                    model_response["model_type"] = pipeline_model["model_type"]
                    model_response["settings"] = pipeline_model["settings"]
                    model_response["name"] = model["name"]
                    model_response["id"] = model["id"]
                    response[step].append(model_response)

        return response


@ns.route("/<int:schema_id>")
@ns.doc(params={"schema_id": "A Schema ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaUpdateResource(SchemaBaseRoute):

    @ns.doc(description="Update schema by schema ID")
    @ns.doc(
        params={
            "schema_id": {
                "type": "integer",
                "required": True,
                "description": "ID of the schema to be updated.",
            },
        }
    )
    @ns.expect(schema_input_dto)
    @ns.marshal_with(schema_output_dto)
    def put(self, schema_id):
        """
        Update the schema by adding or removing mentions, relations, and constraints.
        """
        if not schema_id:
            raise BadRequest("Schema ID is required.")

        data = request.get_json()
        response = self.service.update_schema(data, schema_id)
        return response
