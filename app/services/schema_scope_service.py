import random

from werkzeug.exceptions import BadRequest, Conflict
from app.repositories.schema_scope_repository import SchemaScopeRepository


class SchemaScopeService:
    __schema_scope_repository: SchemaScopeRepository

    def __init__(self, schema_scope_repository):
        self.__schema_scope_repository = schema_scope_repository

    def create_scope_schema(self, schema_id, schema_scopes, schema_scope_constraints):
        if self.__has_duplicates(schema_scopes, key="type"):
            raise Conflict("Duplicate scopes found in schema.")
        if self.__has_duplicates(
            schema_scope_constraints,
            key=lambda x: (
                x["parent_type"],
                x["child_type"],
            ),
        ):
            raise Conflict("Duplicate scope constraints found in schema.")

        root = self.__create_schema_scope(schema_id, "root", "Root")
        schema_scopes_by_type = {"root": root}
        for schema_scope in schema_scopes:
            if schema_scope.get("type") == "root":
                raise BadRequest("Type root not allowed")
            created_scope = self.__create_schema_scope(
                schema_id,
                schema_scope.get("type"),
                schema_scope.get("description"),
                schema_scope.get("color"),
            )
            schema_scopes_by_type[schema_scope["type"]] = created_scope

        for schema_scope_constraint in schema_scope_constraints:
            self.__create_schema_scope_constraint(
                schema_scopes_by_type[schema_scope_constraint.get("parent_type")].id,
                schema_scopes_by_type[schema_scope_constraint.get("child_type")].id,
                schema_scope_constraint.get("merge_consecutive_children"),
            )

    def __has_duplicates(self, items, key):
        seen = set()
        for item in items:
            identifier = key(item) if callable(key) else item[key]
            if identifier in seen:
                return True
            seen.add(identifier)
        return False

    def __create_schema_scope(self, schema_id, scope_type, description, color=None):
        if not color:
            color = self.generate_random_hex_color()
        return self.__schema_scope_repository.create_schema_scope(
            schema_id, scope_type, description, color
        )

    def generate_random_hex_color(self):
        """
        Generate a random hexadecimal color code.
        :return: Random hexadecimal color code
        """
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def __create_schema_scope_constraint(
        self, parent_scope_id, child_scope_id, merge_consecutive_children
    ):
        return self.__schema_scope_repository.create_schema_scope_constraint(
            parent_id=parent_scope_id,
            child_id=child_scope_id,
            merge_consecutive_children=merge_consecutive_children,
        )

    def get_schema_scopes_by_schema_id(self, schema_id):
        schema_scopes = self.__schema_scope_repository.get_schema_scopes_by_schema_id(
            schema_id
        )
        if schema_scopes is None:
            raise BadRequest("No Schema Scopes Found")
        return [s.to_json() for s in schema_scopes]

    def get_schema_scope_constraints_by_schema_id(self, schema_id):
        schema_scope_constraints = (
            self.__schema_scope_repository.get_schema_scope_constraints_by_schema_id(
                schema_id
            )
        )
        if schema_scope_constraints is None:
            raise BadRequest("No Schema Scope Constraints Found")
        return [s.to_json() for s in schema_scope_constraints]

    def get_schema_scope_by_id(self, schema_scope_id):
        return self.__schema_scope_repository.get_schema_scope_by_id(schema_scope_id)

    def get_schema_scope_root_by_schema_id(self, schema_id):
        return self.__schema_scope_repository.get_schema_scope_root_by_schema_id(
            schema_id
        )


schema_scope_service = SchemaScopeService(SchemaScopeRepository())
