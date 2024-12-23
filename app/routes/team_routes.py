from sqlalchemy import exc
from werkzeug.exceptions import BadRequest
from flask_restx import Resource, Namespace
from flask import request
from app.dtos import team_input_dto, team_output_dto
from app.services.team_service import team_service

ns = Namespace("teams", description="Team related operations")


@ns.route("/")
@ns.response(400, "Invalid input")
@ns.response(403, "Authorization required")
@ns.response(404, "Data not found")
class TeamRoutes(Resource):
    service = team_service

    @ns.doc(description="Create a new team")
    @ns.expect(team_input_dto, validate=True)
    @ns.marshal_with(team_output_dto)
    def post(self):
        try:
            request_data = request.get_json()

            response = self.service.create_team(
                request_data["name"],
            )

            return response

        except exc.IntegrityError:
            raise BadRequest("Teamname already exists")
