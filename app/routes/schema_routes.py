from flask import request
from werkzeug.exceptions import BadRequest
from flask_restx import Resource, Namespace

from app.db import transactional
from app.dtos import (
    schema_output_dto,
    schema_output_list_dto,
    model_train_input,
    model_train_output_list_dto,
)
from app.services.schema_service import schema_service
from flask_jwt_extended import jwt_required

ns = Namespace("schemas", description="Schema related operations")


@ns.route("")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaResource(Resource):
    service = schema_service

    @jwt_required()
    @ns.doc(description="Fetch all schemas of current logged-in user")
    @ns.marshal_with(schema_output_list_dto)
    def get(self):
        return self.service.get_schemas_by_user()


@ns.route("/<int:schema_id>")
@ns.doc(params={"schema_id": "A Schema ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaQueryResource(Resource):
    service = schema_service

    @jwt_required()
    @ns.doc(description="Get schema by schema ID")
    @ns.marshal_with(schema_output_dto)
    def get(self, schema_id):
        if not schema_id:
            raise BadRequest("Schema ID is required.")

        response = self.service.get_schema_by_id(schema_id)
        return response


@ns.route("/<int:schema_id>/train")
@ns.doc(params={"schema_id": "A Schema ID"})
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class SchemaTrainResource(Resource):
    service = schema_service

    @jwt_required()
    @transactional
    @ns.doc(description="Get schema by schema ID")
    @ns.expect(model_train_input)
    @ns.marshal_with(model_train_output_list_dto)
    def post(self, schema_id):
        if not schema_id:
            raise BadRequest("Schema ID is required.")

        data = request.json

        response = self.service.train_model_for_schema(
            schema_id, data["model_name"], data["model_type"], data["model_steps"]
        )
        return response
