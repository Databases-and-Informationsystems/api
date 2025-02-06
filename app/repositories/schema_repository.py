from sqlalchemy.orm import aliased
from werkzeug.exceptions import BadRequest
import logging

from app.models import (
    Schema,
    Team,
    ModellingLanguage,
    SchemaMention,
    SchemaRelation,
    SchemaConstraint,
    UserTeam,
    Project,
    DocumentEdit,
    RecommendationModel,
    ModelStep,
    Document,
)
from app.repositories.base_repository import BaseRepository
from flask import request, jsonify


class SchemaRepository(BaseRepository):
    def get_schema_by_id(self, schema_id):
        return (
            self.get_session()
            .query(
                Schema.id,
                Schema.isFixed,
                Schema.team_id,
                Schema.name,
                Team.name.label("team_name"),
                ModellingLanguage.type.label("modelling_language"),
            )
            .join(Team, Schema.team_id == Team.id)
            .join(
                ModellingLanguage, ModellingLanguage.id == Schema.modellingLanguage_id
            )
            .filter((Schema.id == schema_id) & (Schema.active == True))
            .first()
        )

    def get_schema_ids_by_user(self, user_id):
        return (
            self.get_session()
            .query(Schema.id)
            .select_from(UserTeam)
            .join(Schema, Schema.team_id == UserTeam.team_id)
            .filter((UserTeam.user_id == user_id) & (Schema.active == True))
            .all()
        )

    def get_schema_mentions_by_schema(self, schema_id):
        return (
            self.get_session()
            .query(SchemaMention)
            .filter(SchemaMention.schema_id == schema_id)
            .all()
        )

    def get_schema_relations_by_schema(self, schema_id):

        schema_relations = (
            self.get_session()
            .query(SchemaRelation)
            .filter(SchemaRelation.schema_id == schema_id)
            .all()
        )

        logging.debug(f"Schema Relations Retrieved: {schema_relations}")
        logging.debug(f"Type of Retrieved Schema Relations: {type(schema_relations)}")

        return schema_relations

    def get_by_project(self, project_id):
        return (
            self.get_session()
            .query(
                Schema.id,
                Schema.isFixed,
                Schema.team_id,
                Schema.name,
                Team.name.label("team_name"),
                ModellingLanguage.type.label("modelling_language"),
            )
            .join(Team, Schema.team_id == Team.id)
            .join(
                ModellingLanguage, ModellingLanguage.id == Schema.modellingLanguage_id
            )
            .join(Project, Project.schema_id == Schema.id)
            .filter(Project.id == project_id)
            .first()
        )

    def get_schema_constraints_by_schema(self, schema_id):
        mention_head = aliased(SchemaMention)
        mention_tail = aliased(SchemaMention)
        return (
            self.get_session()
            .query(
                SchemaConstraint.id,
                SchemaConstraint.isDirected,
                SchemaRelation.id.label("relation_id"),
                SchemaRelation.tag.label("relation_tag"),
                SchemaRelation.description.label("relation_description"),
                mention_head.id.label("mention_head_id"),
                mention_tail.id.label("mention_tail_id"),
                mention_head.tag.label("mention_head_tag"),
                mention_tail.tag.label("mention_tail_tag"),
                mention_head.description.label("mention_head_description"),
                mention_tail.description.label("mention_tail_description"),
                mention_head.color.label("mention_head_color"),
                mention_tail.color.label("mention_tail_color"),
                mention_head.entityPossible.label("mention_head_entityPossible"),
                mention_tail.entityPossible.label("mention_tail_entityPossible"),
            )
            .join(
                mention_head,
                mention_head.id == SchemaConstraint.schema_mention_id_head,
            )
            .join(
                mention_tail,
                mention_tail.id == SchemaConstraint.schema_mention_id_tail,
            )
            .join(
                SchemaRelation, SchemaRelation.id == SchemaConstraint.schema_relation_id
            )
            .filter(
                (SchemaRelation.schema_id == schema_id)
                & (SchemaConstraint.schema_relation_id == SchemaRelation.id)
            )
            .all()
        )

    def create_schema(
        self, modelling_language_id: int, team_id: int, name: str
    ) -> Schema:
        return super().store_object(
            Schema(
                modellingLanguage_id=modelling_language_id,
                team_id=team_id,
                active=True,
                name=name,
            )
        )

    def create_schema_mention(
        self,
        schema_id: int,
        tag: str,
        description: str,
        entity_possible: bool,
        color: str,
    ) -> SchemaMention:
        return super().store_object(
            SchemaMention(
                schema_id=schema_id,
                tag=tag,
                description=description,
                entityPossible=entity_possible,
                color=color,
            )
        )

    def create_schema_relation(
        self, schema_id: int, tag: str, description: str
    ) -> SchemaRelation:
        return super().store_object(
            SchemaRelation(schema_id=schema_id, tag=tag, description=description)
        )

    def create_schema_constraint(
        self,
        schema_relation_id: int,
        schema_mention_id_head: int,
        schema_mention_id_tail: int,
        is_directed: bool,
    ) -> SchemaConstraint:
        return super().store_object(
            SchemaConstraint(
                schema_relation_id=schema_relation_id,
                schema_mention_id_head=schema_mention_id_head,
                schema_mention_id_tail=schema_mention_id_tail,
                isDirected=is_directed,
            )
        )

    def get_schema_mention_by_schema_tag(self, schema_id, schema_mention_id):
        return (
            self.get_session()
            .query(SchemaMention)
            .filter(
                SchemaMention.schema_id == schema_id,
                SchemaMention.id == schema_mention_id,
            )
            .first()
        )

    def get_schema_by_document_edit(self, document_edit_id):
        return (
            self.get_session()
            .query(Schema)
            .select_from(DocumentEdit)
            .join(Schema, Schema.id == DocumentEdit.schema_id)
            .filter(DocumentEdit.id == document_edit_id)
            .first()
        )

    def fix_schema(self, schema_id):
        self.get_session().query(Schema).filter_by(id=schema_id).update(
            {"isFixed": True}
        )

    def get_schema_mention_by_id(self, schema_mention_id):
        return (
            self.get_session()
            .query(SchemaMention)
            .filter_by(id=schema_mention_id)
            .first()
        )

    def get_schema_relation_by_id(self, schema_relation_id):
        return (
            self.get_session()
            .query(SchemaRelation)
            .filter_by(id=schema_relation_id)
            .first()
        )

    def get_modelling_laguage_by_name(self, modelling_language_name):
        return (
            self.get_session()
            .query(ModellingLanguage)
            .filter_by(type=modelling_language_name)
            .first()
        )

    def add_model_to_schema(self, schema_id, model_name, model_type, step_id):
        model = RecommendationModel(
            model_name=model_name,
            model_type=model_type,
            schema_id=schema_id,
            model_step_id=step_id,
        )
        self.store_object(model)
        return model

    def get_models_by_schema(self, schema_id):
        return (
            self.get_session()
            .query(
                RecommendationModel.id,
                RecommendationModel.model_name,
                RecommendationModel.model_type,
                RecommendationModel.schema_id,
                RecommendationModel.model_step_id,
                ModelStep.type.label("model_step_name"),
            )
            .filter_by(schema_id=schema_id)
            .join(ModelStep, ModelStep.id == RecommendationModel.model_step_id)
            .all()
        )

    def get_model_by_name(self, model_name):
        return (
            self.get_session()
            .query(RecommendationModel)
            .filter_by(model_name=model_name)
            .first()
        )

    def get_model_steps(self):
        return self.get_session().query(ModelStep.id, ModelStep.type).all()

    def get_schema_by_document(self, document_id):
        return (
            self.get_session()
            .query(Schema)
            .select_from(Document)
            .join(Project, Project.id == Document.project_id)
            .join(Schema, Schema.id == Project.schema_id)
            .filter(Document.id == document_id)
            .one()
        )

    def delete_all_constraints(self, schema_id):
        constraints = (
            self.get_session()
            .query(SchemaConstraint)
            .join(
                SchemaRelation, SchemaRelation.id == SchemaConstraint.schema_relation_id
            )
            .filter(SchemaRelation.schema_id == schema_id)
            .all()
        )
        for constraint in constraints:
            self.get_session().delete(constraint)
        self.get_session().flush()

    def delete_all_relations(self, schema_id):
        self.get_session().query(SchemaRelation).filter(
            SchemaRelation.schema_id == schema_id
        ).delete(synchronize_session=False)
        self.get_session().flush()

    def delete_all_mentions(self, schema_id):
        self.get_session().query(SchemaMention).filter(
            SchemaMention.schema_id == schema_id
        ).delete(synchronize_session=False)
        self.get_session().flush()

    def update_schema(self, schema_id, modelling_language_id, name):
        self.get_session().query(Schema).filter(Schema.id == schema_id).update(
            {Schema.modellingLanguage_id: modelling_language_id, Schema.name: name}
        )
        self.get_session().flush()
