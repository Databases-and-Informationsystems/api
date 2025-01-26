from sqlalchemy import text

from app.db import db, Session


class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)


class Team(db.Model):
    __tablename__ = "Team"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )


class UserTeam(db.Model):
    __tablename__ = "UserTeam"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("Team.id"), nullable=False)


class Schema(db.Model):
    __tablename__ = "Schema"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=False, nullable=False)
    isFixed = db.Column(db.Boolean, nullable=False, default=False)
    modellingLanguage_id = db.Column(
        db.Integer, db.ForeignKey("ModellingLanguage.id"), nullable=False
    )
    team_id = db.Column(db.Integer, db.ForeignKey("Team.id"), nullable=False)
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )


class SchemaMention(db.Model):
    __tablename__ = "SchemaMention"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    tag = db.Column(db.String, nullable=False)
    entityPossible = db.Column(db.Boolean, nullable=False, default=True)
    color = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)


class SchemaRelation(db.Model):
    __tablename__ = "SchemaRelation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    tag = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)


class SchemaConstraint(db.Model):
    __tablename__ = "SchemaConstraint"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_relation_id = db.Column(
        db.Integer, db.ForeignKey("SchemaRelation.id"), nullable=False
    )
    schema_mention_id_head = db.Column(db.Integer, nullable=False)
    schema_mention_id_tail = db.Column(db.Integer, nullable=False)
    isDirected = db.Column(db.Boolean, nullable=False, default=True)


class Project(db.Model):
    __tablename__ = "Project"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("Team.id"), nullable=False)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )


class Document(db.Model):
    __tablename__ = "Document"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=False, nullable=False)
    content = db.Column(db.String(), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey("DocumentState.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("Project.id"), nullable=False)
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )


class DocumentRecommendation(db.Model):
    __tablename__ = "DocumentRecommendation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentEditHash = db.Column(db.String(), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("Document.id"), nullable=True)
    document_edit_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEdit.id"), nullable=True
    )
    state_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEditState.id"), nullable=False
    )


class ModelStep(db.Model):
    __tablename__ = "ModelStep"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(), nullable=False)


class RecommendationModel(db.Model):
    """
    Stores available models for recommendations per schema.

    If one model is allowed for multiple steps, multiple entries will be stored in this table.
    """

    __tablename__ = "RecommendationModel"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(
        db.String(),
        unique=False,
        nullable=False,
    )
    model_type = db.Column(
        db.String(),
        unique=False,
        nullable=False,
        comment="options are defined by the pipeline microservices",
    )
    model_step_id = db.Column(db.Integer, db.ForeignKey("ModelStep.id"), nullable=False)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)


class DocumentEdit(db.Model):
    __tablename__ = "DocumentEdit"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    state_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEditState.id"), nullable=False
    )
    document_id = db.Column(db.Integer, db.ForeignKey("Document.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )
    mention_model_id = db.Column(db.Integer, db.ForeignKey("RecommendationModel.id"))
    entity_model_id = db.Column(db.Integer, db.ForeignKey("RecommendationModel.id"))
    relation_model_id = db.Column(db.Integer, db.ForeignKey("RecommendationModel.id"))


class Token(db.Model):
    __tablename__ = "Token"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(), nullable=False)
    document_index = db.Column(db.Integer, nullable=False)
    sentence_index = db.Column(db.Integer, nullable=False)
    pos_tag = db.Column(db.String(), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey("Document.id"), nullable=False)


class Mention(db.Model):
    __tablename__ = "Mention"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_mention_id = db.Column(
        db.Integer, db.ForeignKey("SchemaMention.id"), nullable=False
    )
    isShownRecommendation = db.Column(db.Boolean, nullable=False, default=False)
    document_edit_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEdit.id"), nullable=True
    )
    document_recommendation_id = db.Column(
        db.Integer, db.ForeignKey("DocumentRecommendation.id"), nullable=True
    )
    entity_id = db.Column(db.Integer, db.ForeignKey("Entity.id"), nullable=True)


class TokenMention(db.Model):
    __tablename__ = "TokenMention"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token_id = db.Column(db.Integer, db.ForeignKey("Token.id"), nullable=False)
    mention_id = db.Column(db.Integer, db.ForeignKey("Mention.id"), nullable=False)


class Entity(db.Model):
    __tablename__ = "Entity"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isShownRecommendation = db.Column(db.Boolean, nullable=False, default=False)
    document_edit_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEdit.id"), nullable=True
    )
    document_recommendation_id = db.Column(
        db.Integer, db.ForeignKey("DocumentRecommendation.id"), nullable=True
    )


class Relation(db.Model):
    __tablename__ = "Relation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isShownRecommendation = db.Column(db.Boolean, nullable=False, default=False)
    schema_relation_id = db.Column(
        db.Integer, db.ForeignKey("SchemaRelation.id"), nullable=False
    )
    isDirected = db.Column(db.Boolean, nullable=False, default=True)
    mention_head_id = db.Column(db.Integer, db.ForeignKey("Mention.id"), nullable=False)
    mention_tail_id = db.Column(db.Integer, db.ForeignKey("Mention.id"), nullable=False)
    document_edit_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEdit.id"), nullable=True
    )
    document_recommendation_id = db.Column(
        db.Integer, db.ForeignKey("DocumentRecommendation.id"), nullable=True
    )


class ModellingLanguage(db.Model):
    __tablename__ = "ModellingLanguage"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(), unique=True, nullable=False)


class DocumentState(db.Model):
    __tablename__ = "DocumentState"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(), unique=True, nullable=False)


class DocumentEditState(db.Model):
    __tablename__ = "DocumentEditState"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(), unique=True, nullable=False)

class DocumentEditModelSettings(db.Model):
    __tablename__ = "DocumentEditModelSettings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_edit_id = db.Column(
        db.Integer, db.ForeignKey("DocumentEdit.id"), nullable=False
    )
    recommendation_model_id = db.Column(
        db.Integer, db.ForeignKey("RecommendationModel.id"), nullable=False
    )
    key = db.Column(db.String(), unique=False, nullable=False)
    value = db.Column(db.String(), unique=False, nullable=False)
