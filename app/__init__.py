from flask import Flask
from dotenv import load_dotenv

from flask_migrate import Migrate


def create_app(config_class):
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(config_class)

    # Register blueprints
    from .extension import main, api

    app.register_blueprint(main)
    from app.routes.project_routes import ns as projects
    from app.routes.mention_routes import ns as mentions
    from app.routes.relation_routes import ns as relations
    from app.routes.entity_routes import ns as entities
    from app.routes.document_routes import ns as documents
    from app.routes.schema_routes import ns as schemas
    from app.routes.team_routes import ns as teams
    from app.routes.document_edit_routes import ns as document_edit
    from app.routes.auth_routes import  ns as auth

    api.add_namespace(projects, path="/projects")
    api.add_namespace(mentions, path="/mentions")
    api.add_namespace(relations, path="/relations")
    api.add_namespace(entities, path="/entities")
    api.add_namespace(documents, path="/documents")
    api.add_namespace(schemas, path="/schemas")
    api.add_namespace(teams, path="/teams")
    api.add_namespace(document_edit, path="/document_edits")
    api.add_namespace(auth, path="/auth")

    if not config_class.TESTING:
        from app.db import db

        db.init_app(app)
        Migrate(app, db)
        with app.app_context():
            db.create_all()

    return app
