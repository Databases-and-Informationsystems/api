import requests
from flask import request, current_app
from flask_restx import Namespace
from werkzeug.exceptions import BadRequest

from app.dtos import (
    model_train_input,
    model_train_output_list_dto,
    get_train_models_output_dto,
)
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.train_service import TrainService, train_service

ns = Namespace("training", description="Model training related operations")


class TrainBaseRoute(AuthorizedBaseRoute):
    service: TrainService = train_service


@ns.route("/<int:schema_id>/train")
@ns.doc(params={"schema_id": "A Schema ID"})
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TrainResource(TrainBaseRoute):

    @ns.expect(model_train_input)
    @ns.marshal_with(model_train_output_list_dto)
    def post(self, schema_id):
        """
        Train a recommendation model for a given schema ID
        """
        data = request.json

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_schema_accessible(user_id, schema_id)

        response = self.service.train_model_for_schema(
            schema_id,
            data["model_name"],
            data["model_type"],
            data["model_step"],
            data["document_edits"],
            data["settings"],
        )
        return response

    @ns.marshal_with(get_train_models_output_dto)
    def get(self, schema_id):
        """
        Fetch possible models for training models from pipeline microservice
        """
        user_id = self.user_service.get_user_id()
        self.user_service.check_user_schema_accessible(user_id, schema_id)

        steps = ["mention", "entity", "relation"]
        response = {}

        for index, step in enumerate(steps):
            url = current_app.config.get("PIPELINE_URL") + "/train/" + step
            headers = {"Content-Type": "application/json"}

            train_response = requests.get(url=url, headers=headers)
            if train_response.status_code != 200:
                raise BadRequest("Failed to fetch models: " + train_response.text)

            response[step] = train_response.json()
        return response
