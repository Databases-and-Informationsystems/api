import os


class Config:
    db_user = os.getenv("DB_USER", "user")
    db_password = os.getenv("DB_PASSWORD", "s3cr3t")
    db_host = os.getenv("DB_HOST", "host.docker.internal")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "annotation_db")

    SCOPE_URL = os.getenv(
        "SCOPE_URL", "http://llm-scope-extraction:8888/scope-extractor"
    )
    PIPELINE_URL = os.getenv("PIPELINE_URL", "http://annotation_pipeline:8080/pipeline")
    DIFFERENCE_CALC_URL = os.getenv(
        "DIFFERENCE_CALC_URL", "http://annotation_difference_calc:8443/difference-calc"
    )
    DEBUG = os.getenv("DEBUG", True)

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    RESTX_MASK_SWAGGER = False

    SECRET_KEY = os.getenv("SECRET_KEY", "9384758239485729384728592403484238948235")
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "7328437592749283749238749283748237589437"
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_ALGORITHM = "HS256"


class TestingConfig:
    DEBUG = os.getenv("DEBUG", True)
    PIPELINE_URL = os.getenv("PIPELINE_URL", "http://annotation_pipeline:8080/pipeline")
    TESTING = True
