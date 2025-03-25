import typing

from app.models.buisness_models import BToken
from app.models.db_models import Token, DocumentEdit, TokenMention
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository):
    def create_token(
        self, text, document_index, pos_tag, sentence_index, document_id
    ) -> BToken:
        token = Token(
            text=text,
            document_index=document_index,
            pos_tag=pos_tag,
            sentence_index=sentence_index,
            document_id=document_id,
        )
        return BToken.from_db(super().store_object(token))

    def get_tokens_by_document(self, document_id) -> typing.List[BToken]:
        return [
            BToken.from_db(t)
            for t in (
                self.get_session()
                .query(Token)
                .filter(Token.document_id == document_id)
                .all()
            )
        ]

    def get_tokens_by_mention(self, mention_id) -> typing.List[BToken]:
        return [
            BToken.from_db(t)
            for t in (
                self.get_session()
                .query(Token)
                .join(TokenMention, Token.id == TokenMention.token_id)
                .filter(TokenMention.mention_id == mention_id)
                .all()
            )
        ]

    def get_tokens_by_document_edit(self, document_edit_id) -> typing.List[BToken]:
        return [
            BToken.from_db(t)
            for t in (
                self.get_session()
                .query(Token)
                .select_from(DocumentEdit)
                .join(Token, Token.document_id == DocumentEdit.document_id)
                .filter(DocumentEdit.id == document_edit_id)
                .all()
            )
        ]

    def get_tokens_by_document_ids(self, document_ids):
        return [
            BToken.from_db(t)
            for t in (
                self.get_session()
                .query(Token)
                .filter(Token.document_id.in_(document_ids))
                .all()
            )
        ]
