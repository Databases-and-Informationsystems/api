import os


class Config:
    db_user = os.getenv("DB_USER", "user")
    db_password = os.getenv("DB_PASSWORD", "s3cr3t")
    db_host = os.getenv("DB_HOST", "host.docker.internal")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "annotation_db")

    PIPELINE_URL = "http://host.docker.internal/pipeline"

    DEBUG = os.getenv("DEBUG", True)

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False


class TestingConfig:
    DEBUG = os.getenv("DEBUG", True)
    PIPELINE_URL = "http://host.docker.internal/pipeline"
    TESTING = True
