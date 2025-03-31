import json
import requests
from werkzeug.exceptions import BadRequest, Forbidden
from flask import current_app

from app.models import Token
from app.repositories.token_repository import TokenRepository


class TokenService:
    __token_repository: TokenRepository

    def __init__(self, token_repository):
        self.__token_repository = token_repository

    def tokenize_document(self, doc_id, content):
        """
        Calls tokenization process and stores tokens for document

        :param doc_id: Document ID to tokenize
        :param content: Content of the document
        :return: Token dict
        :raises BadRequest: If tokenization failed
        """
        url = current_app.config.get("PIPELINE_URL") + "/steps/tokenize"
        request_data = json.dumps({"content": content, "document_id": str(doc_id)})
        response = requests.post(
            url=url,
            data=request_data,
            headers={"Content-Type": "application/json"},
        )
        tokens = response.json()
        try:
            for token in tokens:
                self.save_token(
                    token["text"],
                    token["document_index"],
                    token["pos_tag"],
                    token["sentence_index"],
                    doc_id,
                )
        except:
            raise BadRequest("Tokenization failed")
        return {"tokens": tokens}

    def save_token(
        self, text, document_index, pos_tag, sentence_index, doc_id
    ) -> Token:
        """
        Saves token for document, without validation

        :param text: Text of token
        :param document_index: Document index of token
        :param pos_tag: POS tag of token
        :param sentence_index: Sentence index of token
        :param doc_id: document ID
        :return: token database object
        """
        return self.__token_repository.create_token(
            text,
            document_index,
            pos_tag,
            sentence_index,
            doc_id,
        )

    def get_tokens_by_document(self, document_id):
        """
        Fetches all tokens for a document

        :param document_id: Document ID to query tokens
        :return: token_output_list_dto
        """
        tokens = self.__token_repository.get_tokens_by_document(document_id)
        if tokens is None:
            return {"tokens": []}
        return {
            "tokens": [
                {
                    "id": token.id,
                    "text": token.text,
                    "document_index": token.document_index,
                    "sentence_index": token.sentence_index,
                    "pos_tag": token.pos_tag,
                }
                for token in tokens
            ]
        }

    def get_tokens_by_mention(self, mention_id):
        """
        Fetches all tokens for a mention

        :param mention_id: Mention ID to query tokens
        :return: token_output_list_dto
        """
        tokens = self.__token_repository.get_tokens_by_mention(mention_id)
        if tokens is None:
            return {"tokens": []}
        return {
            "tokens": [
                {
                    "id": token.id,
                    "text": token.text,
                    "document_index": token.document_index,
                    "sentence_index": token.sentence_index,
                    "pos_tag": token.pos_tag,
                }
                for token in tokens
            ]
        }

    def check_tokens_in_document_edit(self, token_ids, document_edit_id):
        """
        Checks that tokens are part of document edit

        :param token_ids: Token IDs to check
        :param document_edit_id: Document edit ID to check
        :raises Forbidden: If at least one token is not part of the document
        """
        document_tokens = self.__token_repository.get_tokens_by_document_edit(
            document_edit_id
        )
        document_token_ids = [document_token.id for document_token in document_tokens]
        for token_id in token_ids:
            if token_id not in document_token_ids:
                raise Forbidden("Tokens do not belong to this document.")

    def get_tokens_by_document_ids(self, document_ids):
        """
        Fetch tokens by list of document IDs

        :param document_ids: List of document IDs
        :return: Token dict containing tokens by document ID
        """
        tokens = self.__token_repository.get_tokens_by_document_ids(document_ids)
        document_tokens_dict = {document_id: [] for document_id in document_ids}

        for token in tokens:
            document_tokens_dict[token.document_id].append(
                {
                    "text": token.text,
                    "document_index": token.document_index,
                    "pos_tag": token.pos_tag,
                    "sentence_index": token.sentence_index,
                    "id": token.id,
                }
            )

        return document_tokens_dict

    def get_token_by_id(self, token_id):
        token = self.__token_repository.get_token_by_id(token_id)
        if not token:
            raise BadRequest("Token not found")
        return token


token_service = TokenService(TokenRepository())
