import abc
import dataclasses
import typing
from abc import ABC

from app.db import db
from app.models.db_models import (
    User as DBUser,
    Team as DBTeam,
    ModellingLanguage as DBModellingLanguage,
    SchemaMention as DBSchemaMention,
    SchemaRelation as DBSchemaRelation,
    SchemaConstraint as DBSchemaConstraint,
    Schema as DBSchema,
    Project as DBProject,
    DocumentState as DBDocumentState,
    DocumentEditState as DBDocumentEditState,
    Document as DBDocument,
    Token as DBToken,
    DocumentEdit as DBDocumentEdit,
    Mention as DBMention,
    Relation as DBRelation,
    Entity as DBEntity,
)


class AbstractBusiness(ABC):
    @staticmethod
    def from_db(_object: db.Model):
        pass

    @staticmethod
    def from_json(_json: dict):
        pass

    @abc.abstractmethod
    def to_db(self) -> db.Model:
        pass

    @abc.abstractmethod
    def to_json(self) -> typing.Dict[str, typing.Any]:
        pass


@dataclasses.dataclass
class BUser(AbstractBusiness):
    id: typing.Optional[int]
    username: typing.Optional[str]
    email: str
    password: str

    document_edit_ids: typing.Optional[typing.List[int]] = None
    schema_ids: typing.Optional[typing.List[int]] = None

    def with_document_edits(
        self, document_edits: typing.Optional[typing.List[int]]
    ) -> "BUser":
        self.document_edit_ids = document_edits
        return self

    def with_schemas(self, schema_ids: typing.Optional[typing.List[int]]) -> "BUser":
        self.schema_ids = schema_ids
        return self

    @staticmethod
    def from_db(user: DBUser) -> "BUser":
        return BUser(
            id=user.id, username=user.username, email=user.email, password=user.password
        )

    def to_db(self) -> DBUser:
        return DBUser(
            id=self.id, username=self.username, email=self.email, password=self.password
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }

    @staticmethod
    def from_json(json_data) -> "BUser":
        return BUser(
            id=json_data.get("id", None),
            username=json_data.get("username", None),
            email=json_data.get("email"),
            password=json_data.get("password"),
            document_edit_ids=json_data.get("document_edit_ids", None),
        )

    def as_jwt_content(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": ["user"],
            "document_edit_ids": (
                [de for de in self.document_edit_ids]
                if self.document_edit_ids
                else None
            ),
            "schema_ids": [s for s in self.schema_ids] if self.schema_ids else None,
        }


@dataclasses.dataclass
class BTeam(AbstractBusiness):

    id: typing.Optional[int]
    name: str
    creator: BUser
    members: typing.List[BUser]

    def to_db(self) -> DBTeam:
        return DBTeam(id=self.id, name=self.name, creator_id=self.creator.id)

    @staticmethod
    def from_db(team: DBTeam) -> "BTeam":
        return BTeam(
            id=team.id,
            name=team.name,
            creator=BUser.from_db(team.creator),
            members=[BUser.from_db(member) for member in team.members],
        )

    @staticmethod
    def from_json(json_data) -> "BTeam":
        return BTeam(
            id=json_data.get("id", None),
            name=json_data.get("name"),
            creator=BUser.from_json(json_data.get("creator")),
            members=[BUser.from_json(user) for user in json_data.get("users", [])],
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "name": self.name,
            "creator": self.creator.to_json(),
            "members": [user.to_json() for user in self.members],
        }


@dataclasses.dataclass
class BModellingLanguage(AbstractBusiness):
    id: int
    type: str

    @staticmethod
    def from_db(modelling_language: DBModellingLanguage) -> "BModellingLanguage":
        return BModellingLanguage(
            id=modelling_language.id,
            type=modelling_language.type,
        )

    def to_db(self) -> DBModellingLanguage:
        return DBModellingLanguage(id=self.id, type=self.type)

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "type": self.type,
        }

    @staticmethod
    def from_json(json: dict) -> "BModellingLanguage":
        raise NotImplementedError()


@dataclasses.dataclass
class BToken(AbstractBusiness):
    id: int
    text: str
    document_index: int
    sentence_index: int
    pos_tag: str
    document_id: int

    @staticmethod
    def from_db(token: DBToken) -> "BToken":
        return BToken(
            id=token.id,
            text=token.text,
            document_index=token.document_index,
            sentence_index=token.sentence_index,
            pos_tag=token.pos_tag,
            document_id=token.document_id,
        )

    @staticmethod
    def from_json(json: dict) -> "BToken":
        raise NotImplementedError("TODO")

    def to_db(self) -> DBToken:
        return DBToken(
            id=self.id,
            text=self.text,
            document_index=self.document_index,
            sentence_index=self.sentence_index,
            pos_tag=self.pos_tag,
            document_id=self.document_id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "text": self.text,
            "documentIndex": self.document_index,
            "sentenceIndex": self.sentence_index,
            "posTag": self.pos_tag,
            "document": {"id": self.document_id},
        }


@dataclasses.dataclass
class BSchemaMention(AbstractBusiness):
    id: int
    schema_id: int
    tag: str
    entity_possible: bool
    color: str
    description: str

    tokens = typing.Optional[typing.List[BToken]]

    @staticmethod
    def from_db(schema_mention: DBSchemaMention) -> "BSchemaMention":
        return BSchemaMention(
            id=schema_mention.id,
            schema_id=schema_mention.schema_id,
            tag=schema_mention.tag,
            entity_possible=schema_mention.entityPossible,
            color=schema_mention.color,
            description=schema_mention.description,
        )

    def to_db(self) -> DBSchemaMention:
        return DBSchemaMention(
            id=self.id,
            schema_id=self.schema_id,
            tag=self.tag,
            entityPossible=self.entity_possible,
            color=self.color,
            description=self.description,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "schema": {"id": self.schema_id},
            "tag": self.tag,
            "entityPossible": self.entity_possible,
            "color": self.color,
            "description": self.description,
        }

    @staticmethod
    def from_json(_json: dict) -> "BSchemaMention":
        raise NotImplementedError()


@dataclasses.dataclass
class BSchemaRelation(AbstractBusiness):
    id: int
    schema_id: int
    tag: str
    description: str

    @staticmethod
    def from_db(schema_relation: DBSchemaRelation) -> "BSchemaRelation":
        return BSchemaRelation(
            id=schema_relation.id,
            schema_id=schema_relation.schema_id,
            tag=schema_relation.tag,
            description=schema_relation.description,
        )

    def to_db(self) -> DBSchemaRelation:
        return DBSchemaRelation(
            id=self.id,
            schema_id=self.schema_id,
            tag=self.tag,
            description=self.description,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "schema": {"id": self.schema_id},
            "tag": self.tag,
            "description": self.description,
        }

    @staticmethod
    def from_json(_json: dict) -> "BSchemaRelation":
        raise NotImplementedError()


@dataclasses.dataclass
class BSchemaConstraint(AbstractBusiness):
    id: int
    schema_relation: BSchemaRelation
    schema_head_mention: BSchemaMention
    schema_tail_mention: BSchemaMention
    is_directed: bool

    @staticmethod
    def from_db(schema_constraint: DBSchemaConstraint) -> "BSchemaConstraint":
        return BSchemaConstraint(
            id=schema_constraint.id,
            schema_relation=BSchemaRelation.from_db(schema_constraint.schema_relation),
            schema_head_mention=BSchemaMention.from_db(
                schema_constraint.schema_mention_head
            ),
            schema_tail_mention=BSchemaMention.from_db(
                schema_constraint.schema_mention_tail
            ),
            is_directed=schema_constraint.isDirected,
        )

    def to_db(self) -> DBSchemaConstraint:
        return DBSchemaConstraint(
            id=self.id,
            schema_relation=self.schema_relation.to_db(),
            schema_mention_id_head=self.schema_head_mention.id,
            schema_mention_id_tail=self.schema_tail_mention.id,
            isDirected=self.is_directed,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "schemaRelation": self.schema_relation.to_json(),
            "schemaHeadMention": self.schema_head_mention.to_json(),
            "schemaTailMention": self.schema_tail_mention.to_json(),
            "isDirected": self.is_directed,
        }

    @staticmethod
    def from_json(_json: dict) -> "BSchemaConstraint":
        raise NotImplementedError()


@dataclasses.dataclass
class BSchema(AbstractBusiness):
    id: int
    name: str
    is_fixed: bool
    modelling_language: BModellingLanguage
    team: BTeam

    schema_mentions: typing.Optional[typing.List[BSchemaMention]] = None
    schema_relations: typing.Optional[typing.List[BSchemaRelation]] = None
    schema_constraints: typing.Optional[typing.List[BSchemaConstraint]] = None

    @staticmethod
    def from_db(schema: DBSchema) -> "BSchema":
        return BSchema(
            id=schema.id,
            name=schema.name,
            is_fixed=schema.isFixed,
            modelling_language=BModellingLanguage.from_db(schema.modelling_language),
            team=BTeam.from_db(schema.team),
        )

    def to_db(self) -> DBSchema:
        return DBSchema(
            id=self.id,
            name=self.name,
            isFixed=self.is_fixed,
            modellingLanguage_id=self.modelling_language.id,
            team_id=self.team.id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "isFixed": self.is_fixed,
            "modellingLanguage": self.modelling_language.to_json(),
            "team": self.team.to_json(),
        }

        if self.schema_mentions is not None:
            data["schemaMentions"] = [sm.to_json() for sm in self.schema_mentions]

        if self.schema_relations is not None:
            data["schemaRelations"] = [sr.to_json() for sr in self.schema_relations]

        if self.schema_constraints is not None:
            data["schemaConstraints"] = [sc.to_json() for sc in self.schema_constraints]

        return data

    @staticmethod
    def from_json(_json: dict) -> "BSchema":
        raise NotImplementedError()


@dataclasses.dataclass
class BProject(AbstractBusiness):
    id: int
    name: str
    creator: BUser
    team: BTeam
    schema: BSchema

    @staticmethod
    def from_db(project: db.Model):
        return BProject(
            id=project.id,
            name=project.name,
            creator=BUser.from_db(project.creator),
            team=BTeam.from_db(project.team),
            schema=BSchema.from_db(project.schema),
        )

    def to_db(self) -> db.Model:
        return DBProject(
            id=self.id,
            name=self.name,
            creator_id=self.creator.id,
            team_id=self.team.id,
            schema_id=self.schema.id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "name": self.name,
            "creator": self.creator.to_json(),
            "team": self.team.to_json(),
            "schema": self.schema.to_json(),
        }

    @staticmethod
    def from_json(json: dict):
        pass


@dataclasses.dataclass
class BDocumentState(AbstractBusiness):
    id: int
    type: str

    @staticmethod
    def from_db(document_state: DBDocumentState) -> "BDocumentState":
        return BDocumentState(id=document_state.id, type=document_state.type)

    def to_db(self) -> DBDocumentState:
        return DBDocumentState(id=self.id, type=self.type)

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "type": self.type,
        }

    @staticmethod
    def from_json(json: dict) -> "BDocumentState":
        return BDocumentState(id=json["id"], type=json["type"])


@dataclasses.dataclass
class BDocumentEditState(AbstractBusiness):
    id: int
    type: str

    @staticmethod
    def from_db(document_state: DBDocumentEditState) -> "BDocumentEditState":
        return BDocumentEditState(id=document_state.id, type=document_state.type)

    def to_db(self) -> DBDocumentEditState:
        return DBDocumentEditState(id=self.id, type=self.type)

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "type": self.type,
        }

    @staticmethod
    def from_json(json: dict) -> "BDocumentEditState":
        return BDocumentEditState(id=json["id"], type=json["type"])


@dataclasses.dataclass
class BDocument(AbstractBusiness):
    id: int
    name: str
    content: str
    creator: BUser
    state: BDocumentState
    project: BProject
    document_edits: typing.Optional[typing.List["BDocumentEdit"]] = None
    tokens: typing.Optional[typing.List[BToken]] = None

    def with_document_edits(
        self, document_edits: typing.List["BDocumentEdit"]
    ) -> "BDocument":
        self.document_edits = document_edits
        return self

    def with_tokens(
        self, tokens: typing.Optional[typing.List["BToken"]] = None
    ) -> "BDocument":
        self.tokens = tokens
        return self

    @staticmethod
    def from_db(document: DBDocument) -> "BDocument":
        return BDocument(
            id=document.id,
            name=document.name,
            content=document.content,
            creator=BUser.from_db(document.creator),
            state=BDocumentState.from_db(document.state),
            project=BProject.from_db(document.project),
        )

    def to_db(self) -> DBDocument:
        return DBDocument(
            id=self.id,
            name=self.name,
            content=self.content,
            creator_id=self.creator.id,
            state_id=self.state.id,
            project_id=self.project.id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        res = {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "creator": self.creator.to_json(),
            "state": self.state.to_json(),
            "project": self.project.to_json(),
        }
        if self.document_edits is not None:
            res["documentEdits"] = [de.to_json() for de in self.document_edits]
        if self.tokens is not None:
            res["tokens"] = [t.to_json() for t in self.tokens]
        return res

    @staticmethod
    def from_json(json: dict) -> "BDocument":
        raise NotImplementedError("TODO")


@dataclasses.dataclass
class BMention(AbstractBusiness):
    id: int
    schema_mention: BSchemaMention
    is_shown_recommendation: bool
    document_edit_id: int
    document_recommendation_id: int
    entity_id: int
    tokens: typing.Optional[typing.List[BToken]] = None

    def with_tokens(
        self, tokens: typing.Optional[typing.List["BToken"]] = None
    ) -> "BMention":
        self.tokens = tokens
        return self

    @staticmethod
    def from_db(mention: DBMention) -> "BMention":
        return BMention(
            id=mention.id,
            schema_mention=BSchemaMention.from_db(mention.schema_mention),
            is_shown_recommendation=mention.isShownRecommendation,
            document_edit_id=mention.document_edit_id,
            document_recommendation_id=mention.document_recommendation_id,
            entity_id=mention.entity_id,
            tokens=[BToken.from_db(t) for t in mention.tokens],
        )

    @staticmethod
    def from_json(mention: dict):
        raise NotImplementedError("TODO")

    def to_db(self) -> DBMention:
        return DBMention(
            id=self.id,
            schema_mention_id=self.schema_mention.id,
            isShownRecommendation=self.is_shown_recommendation,
            document_edit_id=self.document_edit_id,
            document_recommendation_id=self.document_recommendation_id,
            entity_id=self.entity_id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        data = {
            "id": self.id,
            "tag": self.schema_mention.tag,
            "schemaMention": self.schema_mention.to_json(),
            "isShownRecommendation": self.is_shown_recommendation,
            "documentEdit": {"id": self.document_edit_id},
            "documentRecommendation": {"id": self.document_recommendation_id},
            "entity": {"id": self.entity_id},
        }
        if self.tokens is not None:
            data["tokens"] = [t.to_json() for t in self.tokens]
        return data


@dataclasses.dataclass
class BRelation(AbstractBusiness):
    id: int
    is_shown_recommendation: bool
    schema_relation: BSchemaRelation
    is_directed: bool
    head_mention: BMention
    tail_mention: BMention
    document_edit_id: int
    document_recommendation_id: int

    @staticmethod
    def from_db(relation: DBRelation) -> "BRelation":
        return BRelation(
            id=relation.id,
            is_shown_recommendation=relation.isShownRecommendation,
            schema_relation=BSchemaRelation.from_db(relation.schema_relation),
            is_directed=relation.isDirected,
            head_mention=BMention.from_db(relation.mention_head),
            tail_mention=BMention.from_db(relation.mention_tail),
            document_edit_id=relation.document_edit_id,
            document_recommendation_id=relation.document_recommendation_id,
        )

    @staticmethod
    def from_json(_json: dict) -> "BRelation":
        raise NotImplementedError("TODO")

    def to_db(self) -> DBRelation:
        return DBRelation(
            id=self.id,
            isShownRecommendation=self.is_shown_recommendation,
            schema_relation=BSchemaRelation.from_db(self.schema_relation),
            isDirected=self.is_directed,
            mention_head_id=self.head_mention.id,
            mention_tail_id=self.tail_mention.id,
            document_edit_id=self.document_edit_id,
            document_recommendation_id=self.document_recommendation_id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "tag": self.schema_relation.tag,
            "isShownRecommendation": self.is_shown_recommendation,
            "schemaRelation": self.schema_relation.to_json(),
            "isDirected": self.is_directed,
            "headMention": self.head_mention.to_json(),
            "tailMention": self.tail_mention.to_json(),
            "documentEdit": {"id": self.document_edit_id},
            "documentRecommendation": {"id": self.document_recommendation_id},
        }


@dataclasses.dataclass
class BEntity(AbstractBusiness):
    id: int
    is_shown_recommendation: bool
    document_edit_id: int
    document_recommendation_id: int
    mentions: typing.Optional[typing.List["BMention"]] = None

    @staticmethod
    def from_db(entity: DBEntity) -> "BEntity":
        return BEntity(
            id=entity.id,
            is_shown_recommendation=entity.isShownRecommendation,
            document_edit_id=entity.document_edit_id,
            document_recommendation_id=entity.document_recommendation_id,
        )

    @staticmethod
    def from_json(json: dict) -> "BEntity":
        raise NotImplementedError("TODO")

    def to_db(self) -> DBEntity:
        return DBEntity(
            id=self.id,
            isShownRecommendation=self.is_shown_recommendation,
            document_edit_id=self.document_edit_id,
            document_recommendation_id=self.document_recommendation_id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        data = {
            "id": self.id,
            "isShownRecommendation": self.is_shown_recommendation,
            "documentEdit": {"id": self.document_edit_id},
            "documentRecommendation": {"id": self.document_recommendation_id},
        }
        if self.mentions is not None:
            data["mentions"] = [m.to_json() for m in self.mentions]

        return data


@dataclasses.dataclass
class BDocumentEdit(AbstractBusiness):
    id: int
    state: BDocumentEditState
    document: BDocument
    user: BUser
    schema: BSchema

    mentions: typing.Optional[typing.List[BMention]] = None
    relations: typing.Optional[typing.List[BRelation]] = None
    entities: typing.Optional[typing.List[BEntity]] = None

    def with_mentions(
        self, mentions: typing.Optional[typing.List[BMention]] = None
    ) -> "BDocumentEdit":
        self.mentions = mentions
        return self

    def with_relations(
        self, relations: typing.Optional[typing.List[BRelation]] = None
    ) -> "BDocumentEdit":
        self.relations = relations
        return self

    def with_entities(
        self, entities: typing.Optional[typing.List[BEntity]] = None
    ) -> "BDocumentEdit":
        self.entities = entities
        return self

    @staticmethod
    def from_db(document_edit: db.Model):
        return BDocumentEdit(
            id=document_edit.id,
            state=BDocumentEditState.from_db(document_edit.state),
            document=BDocument.from_db(document_edit.document),
            user=BUser.from_db(document_edit.user),
            schema=BSchema.from_db(document_edit.schema),
        )

    @staticmethod
    def from_json(_json: dict):
        raise NotImplementedError("TODO")

    def to_db(self) -> DBDocumentEdit:
        return DBDocumentEdit(
            id=self.id,
            state_id=self.state.id,
            document_id=self.document.id,
            user_id=self.user.id,
            schema_id=self.schema.id,
        )

    def to_json(self) -> typing.Dict[str, typing.Any]:
        data = {
            "id": self.id,
            "state": self.state.to_json(),
            "document": self.document.to_json(),
            "user": self.user.to_json(),
            "schema": self.schema.to_json(),
        }

        if self.mentions is not None:
            data["mentions"] = [m.to_json() for m in self.mentions]

        if self.relations is not None:
            data["relations"] = [m.to_json() for m in self.relations]

        if self.entities is not None:
            data["entities"] = [m.to_json() for m in self.entities]

        return data
