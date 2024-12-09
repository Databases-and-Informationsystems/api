from app.models import Token
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository):
    def create_token(self, text, document_index, pos_tag, sentence_index, document_id):
        token = Token(
            text=text,
            document_index=document_index,
            pos_tag=pos_tag,
            sentence_index=sentence_index,
            document_id=document_id,
        )
        super().store_object(token)
        return token
