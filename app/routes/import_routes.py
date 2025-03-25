from flask import request
from flask_restx import Namespace
from werkzeug.exceptions import BadRequest

from app.dtos import document_import_dto
from app.routes.base_routes import AuthorizedBaseRoute
from app.services.import_service import import_service, ImportService

ns = Namespace("imports", description="Import data from different sources")


class ImportBaseRoute(AuthorizedBaseRoute):
    service: ImportService = import_service


@ns.route("/documents")
@ns.response(403, "Authorization required")
class Imports(ImportBaseRoute):

    @ns.doc(description="Import documents from other source.")
    @ns.doc(
        params={
            "project_id": {
                "description": "Target project of the documents. (Defines the target schema)",
                "required": True,
            },
            "source": {
                "description": "Data source type. Only option: 'pet'",
                "required": True,
                "enum": ["pet"],
            },
        }
    )
    @ns.expect(document_import_dto)
    def post(self):
        """
        Import documents from different data sources.
        Currently, only a list of PET documents is supported
        """
        import_list = request.get_json()

        project_id = int(request.args.get("project_id"))
        self.verify_positive_integer(project_id)

        user_id = self.user_service.get_user_id()
        self.user_service.check_user_project_accessible(user_id, project_id)

        source = request.args.get("source")

        if source == "pet":
            return self.service.import_pet_documents(
                import_list["documents"], project_id, user_id
            )
        else:
            raise BadRequest(f"Invalid source {source}")
