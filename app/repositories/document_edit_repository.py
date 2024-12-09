from app.models import DocumentEdit
from app.db import db
from app.repositories.base_repository import BaseRepository


class DocumentEditRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def get_user_id(self, id):
        document_edit = db.session.query(DocumentEdit).get(id)
        return document_edit.user_id
