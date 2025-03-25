import typing

from app.models.buisness_models import BRelation
from app.models.db_models import Relation, SchemaRelation
from app.repositories.base_repository import BaseRepository


class RelationRepository(BaseRepository):

    def create_relation(
        self,
        schema_relation_id,
        document_edit_id,
        is_directed,
        mention_head_id,
        mention_tail_id,
        document_recommendation_id=None,
        is_shown_recommendation=False,
    ):

        relation = Relation(
            schema_relation_id=schema_relation_id,
            document_edit_id=document_edit_id,
            isDirected=is_directed,
            mention_head_id=mention_head_id,
            mention_tail_id=mention_tail_id,
            document_recommendation_id=document_recommendation_id,
            isShownRecommendation=is_shown_recommendation,
        )
        self.store_object(relation)
        return relation

    def get_relations_by_document_edit(
        self, document_edit_id
    ) -> typing.List[BRelation]:
        return [
            BRelation.from_db(r)
            for r in (
                self.get_session()
                .query(
                    Relation,
                )
                .filter(
                    (Relation.document_edit_id == document_edit_id)
                    & (
                        Relation.document_recommendation_id.is_(None)
                        | Relation.isShownRecommendation.is_(True)
                    )
                )
                .all()
            )
        ]

    def get_actual_relations_by_document_edit(
        self, document_edit_id
    ) -> typing.List[BRelation]:
        """

        :param document_edit_id:
        :return: relations including relations where `isShownRecommendation` is false
        """
        return [
            BRelation.from_db(r)
            for r in (
                self.get_session()
                .query(
                    Relation,
                )
                .filter(
                    (Relation.document_edit_id == document_edit_id)
                    & (Relation.document_recommendation_id.is_(None))
                )
                .all()
            )
        ]

    def get_predicted_recommended_relations_by_document_recommendation(
        self, document_recommendation_id
    ):
        return [
            BRelation.from_db(r)
            for r in (
                self.get_session()
                .query(Relation)
                .filter(
                    (Relation.document_recommendation_id == document_recommendation_id)
                )
                .all()
            )
        ]

    def save_relation_in_edit(
        self,
        schema_relation_id,
        is_directed,
        mention_head_id,
        mention_tail_id,
        document_edit_id,
        document_recommendation_id,
        is_shown_recommendation,
    ) -> Relation:
        return super().store_object(
            Relation(
                schema_relation_id=schema_relation_id,
                isDirected=is_directed,
                mention_head_id=mention_head_id,
                mention_tail_id=mention_tail_id,
                document_edit_id=document_edit_id,
                document_recommendation_id=document_recommendation_id,
                isShownRecommendation=is_shown_recommendation,
            )
        )

    def delete_relation_by_id(self, relation_id):
        relation = self.get_session().query(Relation).filter_by(id=relation_id).first()
        if not relation:
            return False
        self.get_session().delete(relation)
        return True

    def get_relation_by_id(self, relation_id):
        relation = (
            self.get_session().query(Relation).filter_by(id=relation_id).one_or_none()
        )
        if relation is None:
            return None
        return BRelation.from_db(relation)

    def get_relations_by_mention(self, mention_id):
        return (
            self.get_session()
            .query(Relation)
            .filter(
                (Relation.mention_head_id == mention_id)
                | (Relation.mention_tail_id == mention_id)
            )
            .filter(
                Relation.document_recommendation_id.is_(None)
                | Relation.isShownRecommendation.is_(True)
            )
            .all()
        )

    def get_relations_by_mention_head_and_tail(
        self, mention_head_id, mention_tail_id
    ) -> typing.List[BRelation]:
        return [
            BRelation.from_db(r)
            for r in (
                self.get_session()
                .query(Relation)
                .filter(
                    (Relation.mention_head_id == mention_head_id)
                    & (Relation.mention_tail_id == mention_tail_id)
                )
                .filter(
                    Relation.document_recommendation_id.is_(None)
                    | Relation.isShownRecommendation.is_(True)
                )
                .all()
            )
        ]

    def delete_relations_by_mention(self, mention_id):
        relations = self.get_relations_by_mention(mention_id)
        for relation in relations:
            self.get_session().delete(relation)

    def update_relation(
        self,
        relation_id,
        schema_relation_id,
        mention_head_id,
        mention_tail_id,
        is_directed,
    ):
        relation = self.get_relation_by_id(relation_id)
        if schema_relation_id:
            relation.schema_relation_id = schema_relation_id
        if mention_head_id:
            relation.mention_head_id = mention_head_id
        if mention_tail_id:
            relation.mention_tail_id = mention_tail_id
        if is_directed is not None:
            relation.isDirected = is_directed

        super().store_object(relation)
        return relation

    def update_is_shown_recommendation(self, relation_id, value):
        """
        Aktualisiert den isShownRecommendation-Wert eines Mention-Eintrags.
        """
        relation = self.get_session().query(Relation).filter_by(id=relation_id).first()
        if relation:
            relation.isShownRecommendation = value
        return relation

    def get_recommendations_by_document_edit(
        self, document_edit_id
    ) -> typing.List[BRelation]:
        return [
            BRelation.from_db(r)
            for r in (
                self.get_session()
                .query(Relation)
                .filter(Relation.document_edit_id == document_edit_id)
                .filter(Relation.isShownRecommendation == True)
                .all()
            )
        ]

    def get_relations_by_edit_ids(self, document_edit_ids):
        return (
            self.get_session()
            .query(
                Relation.id,
                Relation.mention_head_id,
                Relation.mention_tail_id,
                Relation.document_edit_id,
                SchemaRelation.tag,
            )
            .join(SchemaRelation, Relation.schema_relation_id == SchemaRelation.id)
            .filter(Relation.document_edit_id.in_(document_edit_ids))
            .filter(Relation.document_recommendation_id.is_(None))
            .all()
        )
