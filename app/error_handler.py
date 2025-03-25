import traceback

from flask import jsonify, Flask
from flask_restx import ValidationError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:

    @app.errorhandler(Exception)
    def handle_global_error(error):
        if isinstance(error, ValidationError):
            status_code = 400  # Bad Request for ValidationError
        elif isinstance(error, HTTPException):
            status_code = error.code  # Use the code from HTTPException
        else:
            status_code = 500  # Default Internal Server Error
        response = {
            "success": False,
            "type": type(error).__name__,
            "message": str(error),
        }

        # Include traceback only in debug mode
        if app.config.get("DEBUG", False):
            response["traceback"] = traceback.format_exc().splitlines()

        # Attempt to infer an HTTP status code, defaulting to 500
        return jsonify(response), status_code
