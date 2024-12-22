from app.models import Mention
from app.db import db
from app.repositories.base_repository import BaseRepository


class MentionRepository(BaseRepository):
    def __init__(self):
        self.db_session = db.session  # Automatically use the global db.session

    def get_mentions_by_document_edit(self, document_edit_id):
        return (
            self.db_session.query(Mention)
            .filter(
                (Mention.document_edit_id == document_edit_id)
                & (
                    Mention.document_recommendation_id.is_(None)
                    | Mention.isShownRecommendation.is_(True)
                )
            )
            .all()
        )

    def get_mention_by_tag(self, tag):
        return self.db_session.query(Mention).filter_by(tag=tag).all()

    def create_mention(
        self,
        tag,
        document_edit_id=None,
        document_recommendation_id=None,
        is_shown_recommendation=False,
    ):
        mention = Mention(
            document_edit_id=document_edit_id,
            tag=tag,
            document_recommendation_id=document_recommendation_id,
            isShownRecommendation=is_shown_recommendation,
        )
        self.store_object(mention)
        return mention

    def get_mentions_by_document_recommendation(self, document_recommendation_id):
        return (
            self.db_session.query(Mention)
            .filter(Mention.document_recommendation_id == document_recommendation_id)
            .all()
        )
