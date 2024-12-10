from . import document
from flask import request, jsonify, Blueprint
from app.services.document_service import document_service, DocumentService
from werkzeug.exceptions import HTTPException, BadRequest
from flask_jwt_extended import jwt_required, get_jwt_identity

@document.route("/", methods=["POST"])
def fetch_documents_for_user():
    service = document_service

    try:
        request_data = request.get_json()
        if "user_id" not in request_data:
            raise BadRequest("User ID is required.")
        user_id = request_data["user_id"]
        try:
            user_id = int(user_id)
        except:
            raise BadRequest("User ID must be a valid integer.")
        response, status = service.get_documents_by_user(user_id)
        return jsonify(response), status

    except HTTPException as e:
        return {"message": str(e)}, e.code
    except Exception as e:
        return (
            {"message": "An unexpected error occurred.", "details": str(e)},
            500,
        )

# Instantiate a Blueprint for document routes
document = Blueprint("document", __name__)

# Define the upload_document route
@document.route("/", methods=["POST"])
@jwt_required()
def upload_document_route():
    """
    Route to upload a document.
    :return: JSON response with the result
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate input
    if not data:
        return jsonify({"error": "No data received"}), 400

    project_id = data.get("project_id")
    document_name = data.get("name")
    document_content = data.get("content")

    if not project_id or not document_name or not document_content:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Call the service to process the request
        created_document = document_service.upload_document(user_id, project_id, document_name, document_content)
        return jsonify({
            "id": created_document.id,
            "message": "Document uploaded successfully"
        }), 201
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
