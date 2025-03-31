from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import logging

from app.db import add_transaction_wrapper


def create_app(config_class):
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(config_class)
    add_transaction_wrapper(app)
    JWTManager(app)

    logging.basicConfig(
        level=logging.INFO,  # Set the logging level to DEBUG
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        handlers=[logging.StreamHandler()],  # Output logs to the console
    )

    CORS(
        app,
        resources={
            r"/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization"]}
        },
    )

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
    from app.routes.auth_routes import ns as auth
    from app.routes.token_routes import ns as tokens
    from app.routes.import_routes import ns as imports
    from app.routes.train_routes import ns as training
    from app.routes.scope_routes import ns as scopes

    api.add_namespace(projects, path="/projects")
    api.add_namespace(mentions, path="/mentions")
    api.add_namespace(relations, path="/relations")
    api.add_namespace(entities, path="/entities")
    api.add_namespace(documents, path="/documents")
    api.add_namespace(schemas, path="/schemas")
    api.add_namespace(teams, path="/teams")
    api.add_namespace(document_edit, path="/document_edits")
    api.add_namespace(auth, path="/auth")
    api.add_namespace(tokens, path="/tokens")
    api.add_namespace(imports, path="/imports")
    api.add_namespace(training, path="/training")
    api.add_namespace(scopes, path="/scopes")

    if not config_class.TESTING:
        from app.db import db

        db.init_app(app)
        Migrate(app, db)

    return app
