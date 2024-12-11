from flask import Blueprint
from flask_restx import Api


main = Blueprint("main", __name__, url_prefix="/api")
api = Api(
    main,
    title="Annotation Project Backend API",
    version="1.0",
    doc="/docs",
)
