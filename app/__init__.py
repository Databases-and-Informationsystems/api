from flask import Flask
from dotenv import load_dotenv

from .config import Config
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(Config)

    # Register blueprints
    from .routes import main

    app.register_blueprint(main)

    from app.db import db

    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        db.create_all()

    return app
