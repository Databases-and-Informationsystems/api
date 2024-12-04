from app.models import Relation
from app.db import db
from app.repositories.base_repository import BaseRepository


class RelationRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def get_relations_by_document_edit(self, document_edit_id):
        return (
            self.db_session.query(Relation)
            .filter_by(document_edit_id=document_edit_id)
            .all()
        )
