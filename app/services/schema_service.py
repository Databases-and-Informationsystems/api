import random
import re
import typing

from werkzeug.exceptions import BadRequest, Conflict

from app.models.buisness_models import BSchema
from app.models.db_models import Schema, SchemaMention, SchemaRelation, SchemaConstraint
from app.repositories.schema_repository import SchemaRepository


class SchemaService:
    __schema_repository: SchemaRepository

    def __init__(self, schema_repository):
        self.__schema_repository = schema_repository

    def get_schema_by_id(self, schema_id) -> typing.Optional[BSchema]:
        schema = self.__schema_repository.get_schema_by_id(schema_id)
        return self._append_lists_to_schema(schema) if schema else None

    def get_schema_by_project_id(self, project_id) -> BSchema:
        """
        Fetches schema of project with all components
        :param project_id: Project ID to query
        :return: schema_output_dto
        :raises BadRequest: If schema not found
        """
        schema = self.__schema_repository.get_by_project(project_id)
        return self._append_lists_to_schema(schema) if schema else None

    def _append_lists_to_schema(self, schema: BSchema) -> BSchema:
        schema.schema_mentions = self.__schema_repository.get_schema_mentions_by_schema(
            schema.id
        )
        schema.schema_relations = (
            self.__schema_repository.get_schema_relations_by_schema(schema.id)
        )
        schema.schema_constraints = (
            self.__schema_repository.get_schema_constraints_by_schema(schema.id)
        )
        return schema

    def get_schemas_by_user(self, user_id: int) -> typing.List[BSchema]:
        """
        Fetches all schemas a user has access to
        :param user_id: User ID to query
        :return: schema_output_list_dto
        """
        return [
            self._append_lists_to_schema(schema)
            for schema in self.__schema_repository.get_schemas_by_user(user_id)
        ]

    def get_ids_by_user(self, user_id: int) -> typing.List[int]:
        return self.__schema_repository.get_ids_by_user(user_id)

    def __create_schema(self, modelling_language_id, team_id, name) -> Schema:
        """
        Creates a schema, does not validate inputs.
        Adds basic recommendation model for all steps to schema.

        :param modelling_language_id: ID of modelling language
        :param team_id: Team ID
        :param name: Schema name
        :return: Newly created schema
        """
        schema = self.__schema_repository.create_schema(
            modelling_language_id, team_id, name
        )
        steps = self.__schema_repository.get_model_steps()
        steps = [step.type for step in steps]
        schema.models = self.add_model_to_schema(
            schema.id, "OpenAI Large Language Model", "llm", steps
        )
        return schema

    def __create_schema_mention(
        self,
        schema_id: int,
        tag: str,
        description: str,
        entity_possible: bool,
        color: typing.Optional[str] = None,
    ) -> SchemaMention:
        """
        Creates a schema mention, does not validate inputs.

        :param schema_id: Schema ID
        :param tag: Tag of schema mention
        :param description: Description of schema mention
        :param entity_possible: Can mention be part of an entity
        :param color: color for mentions in hex-format. If not specified, random color is chosen
        :return: Newly created schema mention
        """
        if color is None or not self.validate_color_code(color):
            color = self.generate_random_hex_color()
        return self.__schema_repository.create_schema_mention(
            schema_id, tag, description, entity_possible, color
        )

    def __create_schema_relation(
        self, schema_id, tag: str, description: str
    ) -> SchemaRelation:
        """
        Creates a schema relation, does not validate inputs.

        :param schema_id: Schema ID
        :param tag: Tag of schema relation
        :param description: Description of schema relation
        :return: Newly created schema relation
        """
        return self.__schema_repository.create_schema_relation(
            schema_id, tag, description
        )

    def __create_schema_constraint(
        self,
        schema_relation_id: int,
        schema_mention_id_head: int,
        schema_mention_id_tail: int,
        is_directed: bool,
    ) -> SchemaConstraint:
        """
        Creates a schema constraint, does not validate inputs.

        :param schema_relation_id: Schema Relation ID for relation
        :param schema_mention_id_head: Schema Mention ID for head mention
        :param schema_mention_id_tail: Schema Mention ID for tail mention
        :param is_directed: Is relation directed
        :return: Newly created schema constraint
        """
        return self.__schema_repository.create_schema_constraint(
            schema_relation_id,
            schema_mention_id_head,
            schema_mention_id_tail,
            is_directed,
        )

    def verify_constraint(
        self, schema, schema_relation_id, head_schema_mention_id, tail_schema_mention_id
    ) -> any:
        """
        Verifies that a relation conforms to a schema constraint.
        :param schema: schema_output_dto
        :param schema_relation_id: Schema relation ID of the relation
        :param head_schema_mention_id: Schema mention ID of head mention
        :param tail_schema_mention_id: Schema mention ID of tail mention
        :return: Constraint that matches relation
        :raises BadRequest: If no constraint matches
        """
        constraint = next(
            (
                constraint
                for constraint in schema["schema_constraints"]
                if constraint["schema_relation"]["id"] == schema_relation_id
                and (
                    (
                        constraint["schema_mention_head"]["id"]
                        == head_schema_mention_id
                        and constraint["schema_mention_tail"]["id"]
                        == tail_schema_mention_id
                    )
                    or (
                        constraint["schema_mention_tail"]["id"]
                        == head_schema_mention_id
                        and constraint["schema_mention_head"]["id"]
                        == tail_schema_mention_id
                        and constraint["is_directed"] == False
                    )
                )
            ),
            None,
        )
        if constraint is None:
            raise BadRequest(
                "The Relation "
                + str(schema_relation_id)
                + " with mention_head: "
                + str(head_schema_mention_id)
                + " and mention_tail: "
                + str(tail_schema_mention_id)
                + " is not allowed in the schema."
            )

        return constraint

    def generate_random_hex_color(self):
        """
        Generate a random hexadecimal color code.
        :return: Random hexadecimal color code
        """
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def get_schema_by_document_edit(self, document_edit_id) -> Schema:
        """
        Fetch schema database object by document edit ID

        :param document_edit_id: Document Edit ID to query
        :return: Schema database object
        """
        return self.__schema_repository.get_schema_by_document_edit(document_edit_id)

    def fix_schema(self, schema_id):
        """
        Fixes a schema so it cannot be modified.

        :param schema_id: Schema to fix
        """
        self.__schema_repository.fix_schema(schema_id)

    def get_schema_mention_by_id(self, schema_mention_id):
        """
        Fetch schema mention by its ID.

        :param schema_mention_id: Schema mention ID to query
        :return: schema mention database object
        :raises BadRequest: If schema mention does not exist
        """
        schema_mention = self.__schema_repository.get_schema_mention_by_id(
            schema_mention_id
        )
        if schema_mention is None:
            raise BadRequest("Mention Tag not allowed")
        return schema_mention

    def get_schema_relation_by_id(self, schema_relation_id):
        """
        Fetch schema relation by its ID.

        :param schema_relation_id: Schema relation ID to query
        :return: Schema relation database object
        :raises BadRequest: If schema relation does not exist
        """
        schema_relation = self.__schema_repository.get_schema_relation_by_id(
            schema_relation_id
        )
        if schema_relation is None:
            raise BadRequest("Relation Tag not allowed")
        return schema_relation

    def create_extended_schema(self, schema, team_id: int) -> any:
        """
        Creates schema for team with its components.
        Verifies that input is valid.

        :param schema: schema_input_dto
        :param team_id: Team ID to create schema for
        :return: schema_output_dto
        :raises Conflict: If duplicate mention tags, relation tags or constraints detected
        :raises BadRequest: If no matching constraint found or modelling language not supported
        """
        modelling_language = self.__schema_repository.get_modelling_laguage_by_name(
            schema["modelling_language"]
        )
        if modelling_language is None:
            raise BadRequest("Modelling Language not allowed")

        created_schema = self.__create_schema(
            modelling_language.id, team_id, schema["name"]
        )
        self.create_schema_components(schema, created_schema.id)
        return self.get_schema_by_id(created_schema.id)

    def create_schema_components(self, schema, schema_id):
        if self.__has_duplicates(schema["schema_mentions"], key="tag"):
            raise Conflict("Duplicate tags found in schema mentions.")
        if self.__has_duplicates(schema["schema_relations"], key="tag"):
            raise Conflict("Duplicate tags found in schema relations.")
        if self.__has_duplicates(
            schema["schema_constraints"],
            key=lambda x: (
                x["mention_head_tag"],
                x["mention_tail_tag"],
                x["relation_tag"],
            ),
        ):
            raise Conflict("Duplicate constraints found in schema.")

        schema_mentions_by_tag = {}
        for schema_mention in schema["schema_mentions"]:
            created_mention = self.__create_schema_mention(
                schema_id,
                schema_mention.get("tag"),
                schema_mention.get("description"),
                schema_mention.get("entity_possible"),
                schema_mention.get("color"),
            )
            schema_mentions_by_tag[schema_mention["tag"]] = created_mention

        schema_relations_by_tag = {}
        for schema_relation in schema["schema_relations"]:
            created_relation = self.__create_schema_relation(
                schema_id,
                schema_relation.get("tag"),
                schema_relation.get("description"),
            )
            schema_relations_by_tag[schema_relation["tag"]] = created_relation

        try:
            for constraint in schema["schema_constraints"]:
                self.__create_schema_constraint(
                    schema_relations_by_tag[constraint.get("relation_tag")].id,
                    schema_mentions_by_tag[constraint.get("mention_head_tag")].id,
                    schema_mentions_by_tag[constraint.get("mention_tail_tag")].id,
                    constraint.get("is_directed"),
                )
        except KeyError as e:
            raise BadRequest("Constraint not allowed: " + str(e))

    def __has_duplicates(self, items, key):
        seen = set()
        for item in items:
            identifier = key(item) if callable(key) else item[key]
            if identifier in seen:
                return True
            seen.add(identifier)
        return False

    def validate_color_code(self, string):
        """
        Validate whether string is a valid hex color code.
        :param string: string to check
        :return: True if string is a valid hex color code.
        """
        hexa_code = re.compile(r"^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$")
        return bool(re.match(hexa_code, string))

    def check_models_in_schema(
        self, mention_model_id, entity_model_id, relation_model_id, schema_id
    ):
        """
        Checks whether models are part of a schema for specified step.

        :param mention_model_id: Mention model ID to check
        :param entity_model_id: Entity model ID to check
        :param relation_model_id: Relation model ID to check
        :param schema_id: Schema ID to check
        :raise BadRequest: If at least one model not belongs to the schema for given step
        """
        schema_models = self.__schema_repository.get_models_by_schema(schema_id)
        validated = 0
        for schema_model in schema_models:
            if (
                schema_model.id == mention_model_id
                and schema_model.model_step_id == 1  # "MENTIONS"
            ):
                validated += 1
            if (
                schema_model.id == entity_model_id
                and schema_model.model_step_id == 2  # "ENTITIES"
            ):
                validated += 1
            if (
                schema_model.id == relation_model_id
                and schema_model.model_step_id == 3  # "RELATIONS"
            ):
                validated += 1

        if validated != 3:
            raise BadRequest(
                "At least one model not found for given steps in this schema"
            )

    def get_models_by_schema(self, schema_id):
        """
        Fetches all models that can be used for recommendation generation.

        :param schema_id: Schema to query models for
        :return: schema_model_dto
        """
        models = self.__schema_repository.get_models_by_schema(schema_id)
        return [
            {
                "id": model.id,
                "name": model.model_name,
                "type": model.model_type,
                "step": {
                    "id": model.model_step_id,
                    "type": model.model_step_name,
                },
            }
            for model in models
        ]

    def get_schema_mentions_by_schema(self, schema_id):
        schema_mentions = self.__schema_repository.get_schema_mentions_by_schema(
            schema_id
        )
        if schema_mentions is None:
            raise BadRequest("No Schema Mentions Found")
        return schema_mentions

    def get_schema_by_document(self, document_id) -> Schema:
        """
        Fetches schema by document ID.
        :param document_id: Document ID to query
        :return: Schema database object
        """
        return self.__schema_repository.get_schema_by_document(document_id)

    def update_schema(self, schema, schema_id):
        old_schema = self.__schema_repository.get_schema_by_id(schema_id)
        if old_schema.isFixed:
            raise BadRequest("Schema is fixed and cannot be modified.")

        modelling_language = self.__schema_repository.get_modelling_laguage_by_name(
            schema["modelling_language"]
        )
        if modelling_language is None:
            raise BadRequest("Modelling Language not allowed")

        self.__schema_repository.update_schema(
            schema_id, modelling_language.id, schema["name"]
        )

        self.delete_schema_components(schema_id)
        self.create_schema_components(schema, schema_id)
        return self.get_schema_by_id(schema_id)

    def delete_schema_components(self, schema_id):
        self.__schema_repository.delete_all_constraints(schema_id)
        self.__schema_repository.delete_all_relations(schema_id)
        self.__schema_repository.delete_all_mentions(schema_id)

    def get_schema_relations_by_schema(self, schema_id):
        schema_relations = self.__schema_repository.get_schema_relations_by_schema(
            schema_id
        )
        if schema_relations is None:
            raise BadRequest("No Schema Mentions Found")
        return schema_relations

    def get_schema_constraints_by_schema(self, schema_id):
        schema_constraints = self.__schema_repository.get_schema_constraints_by_schema(
            schema_id
        )
        if schema_constraints is None:
            raise BadRequest("No Schema Mentions Found")
        return schema_constraints

    def get_model_by_name(self, model_name):
        """
        Fetches a recommendation model by name.
        :param model_name: Model name
        :return: Recommendation model database object
        """
        return self.__schema_repository.get_model_by_name(model_name)

    def add_model_to_schema(self, schema_id, model_name, model_type, steps):
        """
        Add a recommendation model to a schema.

        :param schema_id: Schema ID
        :param model_name: Model name
        :param model_type: Model type
        :param steps: Step name, allowed: MENTIONS, ENTITIES, RELATIONS
        :return: Newly created recommendation model database object
        :raises BadRequest: If step name is not allowed
        """
        db_steps = self.__schema_repository.get_model_steps()
        step_dict = {}
        for db_step in db_steps:
            step_dict[db_step.type] = db_step.id

        models = []
        for step in steps:
            if step not in step_dict.keys():
                raise BadRequest("Step " + step + " not allowed.")
            model = self.__schema_repository.add_model_to_schema(
                model_name=model_name,
                model_type=model_type,
                schema_id=schema_id,
                step_id=step_dict[step],
            )

            model.model_step_name = step
            models.append(model)
        return models


schema_service = SchemaService(SchemaRepository())
