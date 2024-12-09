from app.repositories.token_mention_repository import TokenMentionRepository


class TokenMentionService:
    __token_mention_repository: TokenMentionRepository

    def __init__(self, token_mention_repository):
        self.__token_mention_repository = token_mention_repository

    def create_token_mention(self, token_id, mention_id):
        return self.__token_mention_repository.create_token_mention(
            token_id, mention_id
        )

    def get_token_mention(self, token_id):
        return self.__token_mention_repository.get_token_mention(token_id)


token_mention_service = TokenMentionService(TokenMentionRepository())
