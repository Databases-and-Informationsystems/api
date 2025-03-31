from app.models import SchemaScope, SchemaScopeConstraint
from app.repositories.base_repository import BaseRepository


class SchemaScopeRepository(BaseRepository):
    def get_schema_scope_by_id(self, schema_scope_id):
        return (
            self.get_session()
            .query(SchemaScope)
            .filter(SchemaScope.id == schema_scope_id)
            .first()
        )

    def create_schema_scope(self, schema_id, scope_type, description, color):
        schema_scope = SchemaScope(
            type=scope_type, description=description, schema_id=schema_id, color=color
        )
        super().store_object(schema_scope)
        return schema_scope

    def create_schema_scope_constraint(self, parent_id, child_id):
        constraint = SchemaScopeConstraint(
            schema_scope_parent_id=parent_id, schema_scope_child_id=child_id
        )
        super().store_object(constraint)
        return constraint

    def get_schema_scopes_by_schema_id(self, schema_id):
        return (
            self.get_session()
            .query(SchemaScope)
            .filter(SchemaScope.schema_id == schema_id)
            .all()
        )

    def get_schema_scope_constraints_by_schema_id(self, schema_id):
        return (
            self.get_session()
            .query(SchemaScopeConstraint)
            .filter(
                SchemaScopeConstraint.schema_scope_parent.has(
                    SchemaScope.schema_id == schema_id
                )
            )
            .all()
        )

    def get_schema_scope_root_by_schema_id(self, schema_id):
        return (
            self.get_session()
            .query(SchemaScope)
            .filter(SchemaScope.schema_id == schema_id)
            .filter(SchemaScope.type == "root")
            .first()
        )
