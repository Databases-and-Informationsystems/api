import typing

from app.models.buisness_models import BMention
from app.models.db_models import Mention, TokenMention, SchemaMention, Token
from app.repositories.base_repository import BaseRepository


class MentionRepository(BaseRepository):

    def get_mentions_with_tokens_by_document_edit(self, document_edit_id):
        results = (
            self.get_session()
            .query(
                Mention.id.label("mention_id"),
                Mention.isShownRecommendation,
                Mention.document_edit_id,
                Mention.document_recommendation_id,
                Mention.entity_id,
                Token.id.label("token_id"),
                Token.text,
                Token.document_index,
                Token.sentence_index,
                Token.pos_tag,
                SchemaMention.id.label("schema_mention_id"),
                SchemaMention.tag,
                SchemaMention.description,
                SchemaMention.color,
                SchemaMention.entityPossible,
            )
            .join(SchemaMention, Mention.schema_mention_id == SchemaMention.id)
            .outerjoin(TokenMention, Mention.id == TokenMention.mention_id)
            .outerjoin(Token, TokenMention.token_id == Token.id)  # Join tokens
            .filter(
                (Mention.document_edit_id == document_edit_id)
                & (
                    Mention.document_recommendation_id.is_(None)
                    | Mention.isShownRecommendation.is_(True)
                )
            )
            .all()
        )
        return results

    def get_actual_mentions_with_tokens_by_document_edit(self, document_edit_id):
        results = (
            self.get_session()
            .query(
                Mention.id.label("mention_id"),
                Mention.document_edit_id,
                Mention.document_recommendation_id,
                SchemaMention.tag,
                Mention.entity_id,
                Token.id.label("token_id"),
                Token.text,
                Token.document_index,
                Token.sentence_index,
                Token.pos_tag,
            )
            .join(SchemaMention, SchemaMention.id == Mention.schema_mention_id)
            .outerjoin(TokenMention, Mention.id == TokenMention.mention_id)
            .outerjoin(Token, TokenMention.token_id == Token.id)  # Join tokens
            .filter(
                (Mention.document_edit_id == document_edit_id)
                & (Mention.document_recommendation_id.is_(None))
            )
            .all()
        )
        return results

    def get_predicted_mentions_with_tokens_by_document_edit(self, document_edit_id):
        results = (
            self.get_session()
            .query(
                Mention.id.label("mention_id"),
                Mention.document_edit_id,
                Mention.document_recommendation_id,
                SchemaMention.tag,
                Mention.entity_id,
                Token.id.label("token_id"),
                Token.text,
                Token.document_index,
                Token.sentence_index,
                Token.pos_tag,
            )
            .join(SchemaMention, SchemaMention.id == Mention.schema_mention_id)
            .outerjoin(TokenMention, Mention.id == TokenMention.mention_id)
            .outerjoin(Token, TokenMention.token_id == Token.id)  # Join tokens
            .filter(
                (Mention.document_edit_id == document_edit_id)
                & (Mention.document_recommendation_id.is_not(None))
            )
            .all()
        )
        return results

    def get_mention_with_schema_by_id(self, mention_id):
        return (
            self.get_session()
            .query(
                Mention.id.label("mention_id"),
                Mention.isShownRecommendation,
                Mention.document_edit_id,
                Mention.document_recommendation_id,
                Mention.entity_id,
                SchemaMention.id.label("schema_mention_id"),
                SchemaMention.tag,
                SchemaMention.description,
                SchemaMention.color,
                SchemaMention.entityPossible,
            )
            .join(SchemaMention, Mention.schema_mention_id == SchemaMention.id)
            .filter(Mention.id == mention_id)
            .first()
        )

    def create_mention(
        self,
        schema_mention_id,
        document_edit_id=None,
        document_recommendation_id=None,
        is_shown_recommendation=False,
        entity_id=None,
    ):
        mention = Mention(
            document_edit_id=document_edit_id,
            schema_mention_id=schema_mention_id,
            document_recommendation_id=document_recommendation_id,
            isShownRecommendation=is_shown_recommendation,
            entity_id=entity_id,
        )
        return self.store_object(mention)

    def get_mentions_by_document_recommendation(self, document_recommendation_id):
        return [
            BMention.from_db(m)
            for m in (
                self.get_session()
                .query(Mention)
                .filter(
                    Mention.document_recommendation_id == document_recommendation_id
                )
                .all()
            )
        ]

    def get_mention_by_id(self, mention_id) -> typing.Optional[BMention]:
        mention = (
            self.get_session().query(Mention).filter_by(id=mention_id).one_or_none()
        )
        if mention is None:
            return None
        return BMention.from_db(mention)

    def delete_mention_by_id(self, mention_id):
        mention = self.get_session().query(Mention).get(mention_id)
        if not mention:
            return False
        tokensMentions = (
            self.get_session().query(TokenMention).filter_by(mention_id=mention_id)
        )
        for tokenMention in tokensMentions:
            self.get_session().delete(tokenMention)

        self.get_session().delete(mention)
        return True

    def set_entity_id_to_null(self, entity_id):
        mentions = (
            self.get_session().query(Mention).filter(Mention.entity_id == entity_id)
        ).all()

        for mention in mentions:
            mention.entity_id = None

        return len(mentions)

    def add_to_entity(self, entity_id: int, mention_id: int):
        self.get_session().query(Mention).filter_by(id=mention_id).update(
            {"entity_id": entity_id}
        )

    def get_mentions_by_entity_id(self, entity_id):
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValueError("Invalid entity ID. It must be a positive integer.")

        return [
            BMention.from_db(m)
            for m in (
                self.get_session()
                .query(Mention)
                .filter(Mention.entity_id == entity_id)
                .all()
            )
        ]

    def update_mention(self, mention_id, schema_mention_id, entity_id):
        mention = self.get_mention_by_id(mention_id)
        if schema_mention_id:
            mention.schema_mention_id = schema_mention_id
        if entity_id:
            mention.entity_id = entity_id
        elif entity_id == 0:
            mention.entity_id = None
        super().store_object(mention)
        return mention

    def update_is_shown_recommendation(self, mention_id, value):
        """
        Aktualisiert den isShownRecommendation-Wert eines Mention-Eintrags.
        """
        mention = self.get_session().query(Mention).filter_by(id=mention_id).first()
        if mention:
            mention.isShownRecommendation = value
        return mention

    def get_recommendations_by_document_edit(self, document_edit_id):
        return [
            BMention.from_db(m)
            for m in (
                self.get_session()
                .query(Mention)
                .filter(Mention.document_edit_id == document_edit_id)
                .filter(Mention.isShownRecommendation == True)
                .all()
            )
        ]

    def get_mentions_by_edit_ids(
        self, document_edit_ids: typing.List[int]
    ) -> typing.List[BMention]:
        return [
            BMention.from_db(mention)
            for mention in (
                self.get_session()
                .query(
                    Mention,
                )
                # .join(SchemaMention, SchemaMention.id == Mention.schema_mention_id)
                # .join(TokenMention, TokenMention.mention_id == Mention.id)
                # .join(Token, Token.id == TokenMention.token_id)
                .filter(Mention.document_edit_id.in_(document_edit_ids))
                .filter(Mention.document_recommendation_id.is_(None))
                .all()
            )
        ]
