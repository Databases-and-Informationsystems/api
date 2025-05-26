from app.models import Scope, SchemaScope
from app.repositories.base_repository import BaseRepository


class ScopeRepository(BaseRepository):
    def create_scope(
        self,
        schema_scope_id,
        token_start_id,
        token_end_id,
        parent_scope_id=None,
        document_edit_id=None,
        document_recommendation_id=None,
    ):
        scope = Scope(
            schema_scope_id=schema_scope_id,
            token_start_id=token_start_id,
            token_end_id=token_end_id,
            parent_scope_id=parent_scope_id,
            document_edit_id=document_edit_id,
            document_recommendation_id=document_recommendation_id,
        )
        scope = self.store_object(scope)
        if parent_scope_id is not None:
            self.get_session().refresh(self.get_object_by_id(Scope, parent_scope_id))
        return scope

    def delete_scope(self, scope_id):
        scope = self.get_session().query(Scope).filter_by(id=scope_id).first()
        if not scope:
            return False
        self.get_session().delete(scope)
        return True

    def update_scope(
        self,
        scope_id,
        schema_scope_id=None,
        token_start_id=None,
        token_end_id=None,
        parent_scope_id=None,
    ):
        scope = self.get_session().query(Scope).filter_by(id=scope_id).first()
        if schema_scope_id:
            scope.schema_scope_id = schema_scope_id
        if token_start_id:
            scope.token_start_id = token_start_id
        if token_end_id:
            scope.token_end_id = token_end_id
        if parent_scope_id:
            scope.parent_scope_id = parent_scope_id
        super().store_object(scope)
        return scope

    def get_scope_tree_by_document_edit(self, document_edit_id):
        return (
            self.get_session()
            .query(Scope)
            .filter(Scope.document_edit_id == document_edit_id)
            .filter(Scope.schema_scope.has(SchemaScope.type == "root"))
            .first()
        )

    def get_scopes_by_document_edit(self, document_edit_id):
        return (
            self.get_session()
            .query(Scope)
            .filter(Scope.document_edit_id == document_edit_id)
            .all()
        )

    def delete_scope_tree(self, document_edit_id):
        scopes = (
            self.get_session()
            .query(Scope)
            .filter_by(document_edit_id=document_edit_id)
            .all()
        )
        for scope in scopes:
            # do not delete root
            if scope.parent_scope_id is not None:
                self.get_session().delete(scope)
        if not scopes:
            return False
        return True
