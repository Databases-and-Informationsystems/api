import typing

from app.models.buisness_models import BEntity
from app.models.db_models import Entity
from app.repositories.base_repository import BaseRepository


class EntityRepository(BaseRepository):

    def create_entity(
        self,
        document_edit_id,
        document_recommendation_id=None,
        is_shown_recommendation=False,
    ) -> BEntity:

        entity = Entity(
            document_edit_id=document_edit_id,
            document_recommendation_id=document_recommendation_id,
            isShownRecommendation=is_shown_recommendation,
        )
        self.store_object(entity)
        return BEntity.from_db(entity)

    def get_entities_by_document_edit(self, document_edit_id) -> typing.List[BEntity]:
        return [
            BEntity.from_db(e)
            for e in (
                self.get_session()
                .query(Entity)
                .filter(
                    (Entity.document_edit_id == document_edit_id)
                    & (
                        Entity.document_recommendation_id.is_(None)
                        | Entity.isShownRecommendation.is_(True)
                    )
                )
                .all()
            )
        ]

    def create_in_edit(self, document_edit_id: int) -> Entity:
        return super().store_object(
            Entity(document_edit_id=document_edit_id, isShownRecommendation=True)
        )

    def delete_entity_by_id(self, entity_id):
        entity = self.get_entity_by_id(entity_id)
        if entity:
            self.get_session().delete(entity)

    def get_entity_by_id(self, entity_id):
        return self.get_session().query(Entity).filter_by(id=entity_id).first()
