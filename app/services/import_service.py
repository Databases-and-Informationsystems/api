import typing

from app.models import Mention
from app.repositories.document_repository import DocumentRepository
from app.repositories.schema_repository import ModellingLanguagesByName
from app.services.document_edit_service import (
    document_edit_service,
    DocumentEditService,
)
from app.services.document_service import DocumentService, document_service
from app.services.entity_service import EntityService, entity_service
from app.services.mention_services import MentionService, mention_service
from app.services.relation_services import RelationService, relation_service
from app.services.schema_service import SchemaService, schema_service
from app.services.token_service import TokenService, token_service
from app.services.user_service import UserService, user_service


def _verify_constraint(
    schema, tag: str, head_mention: Mention, tail_mention: Mention
) -> any:
    schema_head_mention = next(
        (
            mention
            for mention in schema["schema_mentions"]
            if mention["tag"] == head_mention.tag
        ),
        None,
    )

    if schema_head_mention is None:
        # This is a LogicError as the mentions has been saved before
        raise ImportError(
            f'Given Mention type "{head_mention.tag}" does not exist in the schema of the project'
        )

    schema_tail_mention = next(
        (
            mention
            for mention in schema["schema_mentions"]
            if mention["tag"] == tail_mention.tag
        ),
        None,
    )

    if schema_tail_mention is None:
        # This is a LogicError as the mentions has been saved before
        raise ImportError(
            f'Given Mention type "{tail_mention.tag}" does not exist in the schema of the project'
        )

    print(schema["schema_constraints"], flush=True)
    constraint = next(
        (
            constraint
            for constraint in schema["schema_constraints"]
            if constraint["schema_relation"]["tag"] == tag
            and (
                (
                    constraint["schema_mention_head"]["tag"]
                    == schema_head_mention.get("tag")
                    and constraint["schema_mention_tail"]["tag"]
                    == schema_tail_mention.get("tag")
                )
                or (
                    constraint["schema_mention_tail"]["tag"]
                    == schema_head_mention.get("tag")
                    and constraint["schema_mention_head"]["tag"]
                    == schema_tail_mention.get("tag")
                    and constraint["is_directed"] == False
                )
            )
        ),
        None,
    )
    if constraint is None:
        raise ImportError(
            f"The Relation '{tag}' with mention_head: '{schema_head_mention.get("tag")}' and mention_tail: '{schema_tail_mention.get("tag")}' is not allowed in the schema."
        )

    return constraint


class ImportService:
    _document_service: DocumentService
    _document_edit_service: DocumentEditService
    _token_service: TokenService
    _mention_service: MentionService
    _entity_service: EntityService
    _relation_service: RelationService
    _schema_service: SchemaService
    _user_service: UserService

    def __init__(
        self,
        document_service: DocumentService,
        document_edit_service: DocumentEditService,
        token_service: TokenService,
        mention_service: MentionService,
        entity_service: EntityService,
        relation_service: RelationService,
        schema_service: SchemaService,
        user_service: UserService,
    ):
        self._document_service = document_service
        self._document_edit_service = document_edit_service
        self._token_service = token_service
        self._mention_service = mention_service
        self._entity_service = entity_service
        self._relation_service = relation_service
        self._schema_service = schema_service
        self._user_service = user_service

    def import_pet_documents(
        self,
        pet_documents: typing.List[any],
        project_id: int,
        user_id: int,
    ):

        for pet_document in pet_documents:
            self._import_pet_document(pet_document, project_id, user_id)

        return {"count": len(pet_documents), "success": True}

    def _import_pet_document(self, pet_document: any, project_id: int, user_id: int):
        document = self._document_service.save_document(
            pet_document.get("name"),
            pet_document.get("text"),
            project_id,
            user_id,
            DocumentRepository.DOCUMENT_STATE_ID_FINISHED,
        )

        tokens = pet_document.get("tokens")
        token_ids_by_index = {}
        for index, token in enumerate(tokens):
            created_token = self._token_service.save_token(
                text=token.get("text"),
                document_index=token.get("indexInDocument"),
                pos_tag=token.get("posTag"),
                sentence_index=token.get("sentenceIndex"),
                doc_id=document.id,
            )
            token_ids_by_index[index] = created_token.id

        # Create document edit
        document_edit = document_edit_service.create_document_edit(document.id)
        # Import Mentions to documentEdit
        schema = self._schema_service.get_schema_by_project_id(project_id)

        mentions = pet_document.get("mentions")
        mentions_by_index = {}
        for index, mention in enumerate(mentions):
            schema_mention_id = None
            for schema_mention in schema["schema_mentions"]:
                if schema_mention.get("tag") == mention.get("type"):
                    schema_mention_id = schema_mention.get("id")
                    break
            if schema_mention_id is None:
                raise ImportError(
                    f'Given Mention type "{mention.get("type")}" does not exist in the schema of the project'
                )
            created_mention = self._mention_service.create_mentions(
                {
                    "document_edit_id": document_edit["id"],
                    "schema_mention_id": schema_mention_id,
                    "token_ids": [
                        token_ids_by_index.get(t)
                        for t in mention.get("tokenDocumentIndices")
                    ],
                },
            )
            mentions_by_index[index] = created_mention

        # Import Entities of documentEdit
        entities = pet_document.get("entities")
        for entity in entities:
            created_entity = self._entity_service.create_in_edit(document_edit["id"])

            for mention_index in entity["mentionIndices"]:
                self._mention_service.add_to_entity(
                    created_entity.id, mentions_by_index.get(mention_index).id
                )

        # Import Relations of documentEdit
        relations = pet_document.get("relations")
        for relation in relations:
            schema_relation_id = None
            for schema_relation in schema["schema_relations"]:
                if schema_relation.get("tag") == relation.get("type"):
                    schema_relation_id = schema_relation.get("id")
                    break

            if schema_relation_id is None:
                raise ImportError(
                    f'Given Relation type "{relation.get("type")}" does not exist in the schema of the project'
                )

            schema_constraint = _verify_constraint(
                schema,
                relation.get("type"),
                mentions_by_index.get(relation["headMentionIndex"]),
                mentions_by_index.get(relation["tailMentionIndex"]),
            )

            self._relation_service.save_relation_in_edit(
                schema_relation_id,
                schema_constraint["is_directed"],
                mentions_by_index.get(relation["headMentionIndex"]).id,
                mentions_by_index.get(relation["tailMentionIndex"]).id,
                document_edit["id"],
            )

    def import_schema(self, schema, team_id: int) -> any:
        user_id = self._user_service.get_logged_in_user_id()
        self._user_service.check_user_in_team(user_id, team_id)

        modelling_language_id = ModellingLanguagesByName.get(
            schema.get("modelling_language")
        )

        if modelling_language_id is None:
            raise ValueError(
                f"Modelling language {schema.get("modelling_language")} is not supported."
            )

        name = schema.get("name")
        if name is None:
            raise ValueError("Schema name is required.")

        created_schema = self._schema_service.create_schema(
            modelling_language_id, team_id, name
        )

        schema_mentions_by_tag = {}
        for schema_mention in schema["schema_mentions"]:
            created_mention = self._schema_service.create_schema_mention(
                created_schema.id,
                schema_mention["tag"],
                schema_mention["description"],
                schema_mention["entity_possible"],
            )
            schema_mentions_by_tag[schema_mention["tag"]] = created_mention

        schema_relations_by_tag = {}
        for schema_relation in schema["schema_relations"]:
            created_relation = self._schema_service.create_schema_relation(
                created_schema.id,
                schema_relation.get("tag"),
                schema_relation.get("description"),
            )
            schema_relations_by_tag[schema_relation["tag"]] = created_relation

        for constraint in schema["schema_constraints"]:
            self._schema_service.create_schema_constraint(
                schema_relations_by_tag[constraint.get("relation_tag")].id,
                schema_mentions_by_tag[constraint.get("mention_head_tag")].id,
                schema_mentions_by_tag[constraint.get("mention_tail_tag")].id,
                constraint.get("is_directed"),
            )

        return self._schema_service.get_schema_by_id(created_schema.id)


import_service = ImportService(
    document_service=document_service,
    document_edit_service=document_edit_service,
    token_service=token_service,
    mention_service=mention_service,
    entity_service=entity_service,
    relation_service=relation_service,
    schema_service=schema_service,
    user_service=user_service,
)
