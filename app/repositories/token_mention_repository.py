from app.models import TokenMention
from app.db import db
from app.repositories.base_repository import BaseRepository


class TokenMentionRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def create_token_mention(self, token_id, mention_id):
        token_mention = TokenMention(token_id=token_id, mention_id=mention_id)
        token_mention = self.store_object(token_mention)
        return token_mention

    def get_token_mention(self, token_id):
        return self.db_session.query(TokenMention).filter_by(token_id=token_id).first()
