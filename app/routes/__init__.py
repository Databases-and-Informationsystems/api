from flask import Blueprint

main = Blueprint("main", __name__, url_prefix="/api")
project = Blueprint("projects", __name__, url_prefix="/projects")
mentions = Blueprint("mentions", __name__, url_prefix="/mentions")
relations = Blueprint("relations", __name__, url_prefix="/relations")
main.register_blueprint(project)
main.register_blueprint(mentions)
main.register_blueprint(relations)


from . import api_routes, project_routes, mention_routes, relation_routes
