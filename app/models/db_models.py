from sqlalchemy import text

from app.db import db


# Migrated
class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, email={self.email})"


# Migrated
class UserTeam(db.Model):
    __tablename__ = "UserTeam"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("Team.id"), nullable=False)


# Migrated
class Team(db.Model):
    __tablename__ = "Team"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    active = db.Column(
        db.Boolean, nullable=False, default=True, server_default=text("true")
    )

    creator = db.relationship("User", foreign_keys=[creator_id], backref="teams")

    members = db.relationship(
        "User",
        secondary="UserTeam",
        primaryjoin=id == UserTeam.team_id,
        secondaryjoin=User.id == UserTeam.user_id,
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"Team(id={self.id}, name={self.name}, creator={self.creator.__repr__()}, members={[m.__repr__() for m in self.members]})"


# Migrated
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

    team = db.relationship(
        "Team",
        foreign_keys=[team_id],
        backref="constraints_as_head",
    )

    modelling_language = db.relationship(
        "ModellingLanguage",
        foreign_keys=[modellingLanguage_id],
        backref="schemas",
    )


# Migrated
class SchemaMention(db.Model):
    __tablename__ = "SchemaMention"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    tag = db.Column(db.String, nullable=False)
    entityPossible = db.Column(db.Boolean, nullable=False, default=True)
    color = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)


# Migrated
class SchemaRelation(db.Model):
    __tablename__ = "SchemaRelation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("Schema.id"), nullable=False)
    tag = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)


# Migrated
class SchemaConstraint(db.Model):
    __tablename__ = "SchemaConstraint"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schema_relation_id = db.Column(
        db.Integer, db.ForeignKey("SchemaRelation.id"), nullable=False
    )
    schema_mention_id_head = db.Column(
        db.Integer, db.ForeignKey("SchemaMention.id"), nullable=False
    )
    schema_mention_id_tail = db.Column(
        db.Integer, db.ForeignKey("SchemaMention.id"), nullable=False
    )
    isDirected = db.Column(db.Boolean, nullable=False, default=True)

    schema_mention_head = db.relationship(
        "SchemaMention",
        foreign_keys=[schema_mention_id_head],
        backref="constraints_as_head",
    )
    schema_mention_tail = db.relationship(
        "SchemaMention",
        foreign_keys=[schema_mention_id_tail],
        backref="constraints_as_tail",
    )
    schema_relation = db.relationship(
        "SchemaRelation", foreign_keys=[schema_relation_id], backref="constraints"
    )


# Migrated
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

    creator = db.relationship("User", foreign_keys=[creator_id], backref="projects")
    team = db.relationship("Team", foreign_keys=[team_id], backref="projects")
    schema = db.relationship("Schema", foreign_keys=[schema_id], backref="projects")


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

    creator = db.relationship("User", foreign_keys=[creator_id], backref="documents")
    state = db.relationship(
        "DocumentState", foreign_keys=[state_id], backref="documents"
    )
    project = db.relationship("Project", foreign_keys=[project_id], backref="documents")


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

    state = db.relationship(
        "DocumentEditState", foreign_keys=[state_id], backref="document_edits"
    )
    document = db.relationship(
        "Document", foreign_keys=[document_id], backref="document_edits"
    )
    user = db.relationship("User", foreign_keys=[user_id], backref="document_edits")
    schema = db.relationship(
        "Schema", foreign_keys=[schema_id], backref="document_edits"
    )


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

    schema_mention = db.relationship(
        "SchemaMention", foreign_keys=[schema_mention_id], backref="mentions"
    )

    tokens = db.relationship(
        "Token",
        secondary="TokenMention",
        backref=db.backref("mentions", lazy="select"),
        lazy="select",
    )


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

    schema_relation = db.relationship(
        "SchemaRelation", foreign_keys=[schema_relation_id], backref="relations"
    )

    mention_head = db.relationship(
        "Mention", foreign_keys=[mention_head_id], backref="mention_heads"
    )

    mention_tail = db.relationship(
        "Mention", foreign_keys=[mention_tail_id], backref="mention_tails"
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
