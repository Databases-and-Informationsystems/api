from app.models import Token, DocumentEdit, TokenMention
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
        return super().store_object(token)

    def get_tokens_by_document(self, document_id):
        return (
            self.get_session()
            .query(Token)
            .filter(Token.document_id == document_id)
            .all()
        )

    def get_tokens_by_mention(self, mention_id):
        return (
            self.get_session()
            .query(Token)
            .join(TokenMention, Token.id == TokenMention.token_id)
            .filter(TokenMention.mention_id == mention_id)
            .all()
        )

    def get_tokens_by_document_edit(self, document_edit_id):
        return (
            self.get_session()
            .query(Token)
            .select_from(DocumentEdit)
            .join(Token, Token.document_id == DocumentEdit.document_id)
            .filter(DocumentEdit.id == document_edit_id)
            .all()
        )

    def get_tokens_by_document_ids(self, document_ids):
        return (
            self.get_session()
            .query(Token)
            .filter(Token.document_id.in_(document_ids))
            .all()
        )

    def get_token_by_id(self, token_id):
        return self.get_session().query(Token).filter(Token.id == token_id).first()
