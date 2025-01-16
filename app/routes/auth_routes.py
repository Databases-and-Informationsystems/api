from flask import request
from flask_restx import Namespace, Resource
from app.services.user_service import user_service
from app.dtos import signup_input_dto, signup_output_dto, login_output_dto, login_input_dto
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound

ns = Namespace("auth", description="User Authentication related operations")


@ns.route("/signup")
@ns.response(400, "Invalid input")
@ns.response(409, "User already exists")
class SignupRoute(Resource):
    service = user_service

    @ns.doc(description="Sign up a new user")
    @ns.marshal_with(signup_output_dto)
    @ns.expect(signup_input_dto, validate=True)  # Use the DTO here
    def post(self):
        request_data = request.get_json()

        username = request_data.get("username")
        email = request_data.get("email")
        password = request_data.get("password")

        self.service.signup(username, email, password)
        return {"message": "User created successfully"}

@ns.route("/login")
@ns.response(400, "Invalid input")
@ns.response(401, "Unauthorized")
class LoginRoute(Resource):
    service = user_service

    @ns.doc(description="Log in an existing user")
    @ns.marshal_with(login_output_dto)
    @ns.expect(login_input_dto, validate=True)  # Use the DTO here
    def post(self):
        try:
            request_data = request.get_json()
            email = request_data.get("email")
            password = request_data.get("password")

            result = self.service.login(email, password)

            return result, 200

        except Unauthorized as e:
            return {"error": str(e)}, 401
        except Exception as e:
            return {"error": "An unexpected error occurred"}, 500
        
@ns.route("/update-profile")
@ns.response(200, "Profile updated successfully")
@ns.response(400, "Invalid input")
@ns.response(404, "User not found")
class UpdateProfileRoute(Resource):
    def put(self):
        """
        Update user profile information.

        Payload:
        - username (optional)
        - email (optional)
        - password (optional)
        """
        data = request.get_json()
        user_id = request.headers.get("User-ID")  # Assuming User-ID is passed in headers

        if not user_id:
            raise BadRequest("User ID is required in headers.")

        try:
            updated_user = user_service.update_user_data(
                user_id=user_id,
                username=data.get("username"),
                email=data.get("email"),
                password=data.get("password"),
            )
            return {"message": "Profile updated successfully", "user": updated_user}, 200
        except BadRequest as e:
            return {"message": str(e)}, 400
        except NotFound as e:
            return {"message": str(e)}, 404
