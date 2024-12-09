from flask import Flask
from dotenv import load_dotenv

from flask_migrate import Migrate


def create_app(config_class):
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(config_class)

    # Register blueprints
    from .routes import main, project, mentions, relations

    app.register_blueprint(main)

    from .extension import api

    api.init_app(app)

    from .routes.mention_routes import ns

    api.add_namespace(ns, path="/api")

    if not config_class.TESTING:
        from app.db import db

        db.init_app(app)
        Migrate(app, db)
        with app.app_context():
            db.create_all()

    return app
