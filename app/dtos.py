from flask_restx import fields
from app.extension import api

user_output_dto = api.model(
    "UserOutput",
    {
        "id": fields.Integer,
        "username": fields.String,
        "email": fields.String,
    },
)

mention_input_dto = api.model(
    "CreateMentionInput",
    {
        "schema_mention_id": fields.Integer(required=True, min=1),
        "document_edit_id": fields.Integer(required=True, min=1),
        "token_ids": fields.List(fields.Integer, required=True),
    },
)

schema_mention_output_dto = api.model(
    "SchemaMentionOutput",
    {
        "id": fields.Integer,
        "tag": fields.String,
        "description": fields.String,
        "color": fields.String,
        "entityPossible": fields.Boolean,
    },
)

project_input_dto = api.model(
    "ProjectInput",
    {
        "name": fields.String(required=True),
        "team_id": fields.Integer(required=True, min=1),
        "schema_id": fields.Integer(required=True, min=1),
    },
)

team_dto = api.model(
    "Team",
    {
        "id": fields.Integer,
        "name": fields.String,
    },
)

schema_dto = api.model(
    "Schema",
    {
        "id": fields.Integer,
        "name": fields.String,
    },
)

project_dto = api.model(
    "Project",
    {
        "id": fields.Integer,
        "name": fields.String,
    },
)

document_edit_state_dto = api.model(
    "DocumentEditState",
    {
        "id": fields.Integer,
        "state": fields.String,
    },
)

document_output_dto = api.model(
    "DocumentList",
    {
        "id": fields.Integer,
        "content": fields.String,
        "name": fields.String,
        "state": fields.Nested(
            api.model(
                "DocumentState",
                {
                    "id": fields.Integer,
                    "type": fields.String,
                },
            )
        ),
        "project": fields.Nested(project_dto),
        "schema": fields.Nested(schema_dto),
        "team": fields.Nested(team_dto),
        "document_edit": fields.Nested(document_edit_state_dto),
        "creator": fields.Nested(user_output_dto),
        "document_edits": fields.List(
            fields.Nested(
                api.model(
                    "DocumentEdits",
                    {
                        "id": fields.Integer,
                        "user": fields.Nested(user_output_dto),
                        "state": fields.Nested(
                            api.model(
                                "DocumentEditState",
                                {
                                    "id": fields.Integer,
                                    "type": fields.String,
                                },
                            )
                        ),
                    },
                )
            )
        ),
    },
)

document_list_dto = api.model(
    "DocumentOutput",
    {
        "documents": fields.List(fields.Nested(document_output_dto)),
    },
)

entity_input_dto = api.model(
    "EntityInput",
    {
        "document_edit_id": fields.Integer(required=True, min=1),
        "mention_ids": fields.List(fields.Integer, required=True),
    },
)

schema_relation_output_dto = api.model(
    "SchemaRelationOutput",
    {
        "id": fields.Integer,
        "tag": fields.String,
        "description": fields.String,
    },
)

relation_input_dto = api.model(
    "RelationInput",
    {
        "schema_relation_id": fields.Integer(required=True, min=1),
        "document_edit_id": fields.Integer(required=True, min=1),
        "mention_head_id": fields.Integer(required=True, min=1),
        "mention_tail_id": fields.Integer(required=True, min=1),
    },
)

document_create_dto = api.model(
    "DocumentUpload",
    {
        "project_id": fields.Integer(
            required=True, min=1, description="ID of the project"
        ),
        "file_name": fields.String(required=True, description="Name of the document"),
        "file_content": fields.String(
            required=True, description="Content of the document"
        ),
    },
)

document_list_create_dto = api.model(
    "DocumentListUpload",
    {
        "file_name": fields.String(required=True, description="Name of the document"),
        "file_content": fields.String(
            required=True, description="Content of the document"
        ),
    },
)

document_create_output_dto = api.model(
    "DocumentUploadOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "content": fields.String,
        "creator": fields.Nested(user_output_dto),
        "project_id": fields.Integer,
        "state_id": fields.Integer,
    },
)

schema_constraint_output_dto = api.model(
    "SchemaConstraintOutput",
    {
        "id": fields.Integer,
        "is_directed": fields.Boolean,
        "schema_relation": fields.Nested(schema_relation_output_dto),
        "schema_mention_head": fields.Nested(schema_mention_output_dto),
        "schema_mention_tail": fields.Nested(schema_mention_output_dto),
    },
)

model_step_dto = api.model(
    "ModelStep",
    {
        "id": fields.Integer,
        "type": fields.String,
    },
)

schema_model_dto = api.model(
    "SchemaModel",
    {
        "id": fields.Integer,
        "name": fields.String,
        "type": fields.String,
        "step": fields.Nested(model_step_dto),
    },
)

schema_output_dto = api.model(
    "SchemaOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "is_fixed": fields.Boolean,
        "modellingLanguage": fields.String,
        "team_id": fields.Integer,
        "team_name": fields.String,
        "models": fields.List(fields.Nested(schema_model_dto)),
        "schema_mentions": fields.List(fields.Nested(schema_mention_output_dto)),
        "schema_relations": fields.List(fields.Nested(schema_relation_output_dto)),
        "schema_constraints": fields.List(fields.Nested(schema_constraint_output_dto)),
    },
)

schema_mention_input_dto = api.model(
    "SchemaMentionInput",
    {
        "tag": fields.String(required=True),
        "description": fields.String(required=True),
        "color": fields.String(required=False, example="#12AB3C"),
        "entity_possible": fields.Boolean(default=True),
    },
)

schema_relation_input_dto = api.model(
    "SchemaRelationInput",
    {
        "tag": fields.String(required=True),
        "description": fields.String(required=True),
    },
)

schema_constraint_input_dto = api.model(
    "SchemaConstraintInput",
    {
        "is_directed": fields.Boolean(required=True),
        "relation_tag": fields.String(required=True),
        "mention_head_tag": fields.String(required=True),
        "mention_tail_tag": fields.String(required=True),
    },
)

schema_scope_input_dto = api.model(
    "SchemaScopeInput",
    {
        "type": fields.String(required=True),
        "description": fields.String(required=True),
        "color": fields.String(required=False, example="#12AB3C"),
    },
)

schema_scope_constraints_input_dto = api.model(
    "SchemaScopeConstraintInput",
    {
        "parent_type": fields.String(required=True),
        "child_type": fields.String(required=True),
        "merge_consecutive_children": fields.Boolean(default=False),
    },
)

schema_input_dto = api.model(
    "SchemaInput",
    {
        "name": fields.String(required=True),
        "modelling_language": fields.String(required=True),
        "schema_mentions": fields.List(
            fields.Nested(schema_mention_input_dto), required=True
        ),
        "schema_relations": fields.List(
            fields.Nested(schema_relation_input_dto), required=True
        ),
        "schema_constraints": fields.List(
            fields.Nested(schema_constraint_input_dto), required=True
        ),
        "schema_scopes": fields.List(
            fields.Nested(schema_scope_input_dto), required=False
        ),
        "schema_scope_constraints": fields.List(
            fields.Nested(schema_scope_constraints_input_dto), required=False
        ),
    },
)

schema_output_list_dto = api.model(
    "SchemaOutputList",
    {
        "schemas": fields.List(fields.Nested(schema_output_dto)),
    },
)

team_member_input_dto = api.model(
    "TeamMemberInput",
    {
        "user_mail": fields.String(required=True),
    },
)

team_input_dto = api.model(
    "TeamInput",
    {
        "name": fields.String(required=True),
    },
)

team_user_output_dto = api.model(
    "TeamUserOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "creator": fields.Nested(user_output_dto),
        "members": fields.List(fields.Nested(user_output_dto)),
    },
)

recommendation_model_settings_dto = api.model(
    "RecommendationModelParameter",
    {
        "key": fields.String,
        "value": fields.String,
    },
)

document_edit_input_dto = api.model(
    "DocumentInput",
    {
        "document_id": fields.Integer(required=True, min=1),
        "model_mention_id": fields.Integer(required=False),
        "model_settings_mention": fields.List(
            fields.Nested(recommendation_model_settings_dto)
        ),
        "model_entities_id": fields.Integer(required=False),
        "model_settings_entities": fields.List(
            fields.Nested(recommendation_model_settings_dto)
        ),
        "model_relation_id": fields.Integer(required=False),
        "model_settings_relation": fields.List(
            fields.Nested(recommendation_model_settings_dto)
        ),
    },
)

document_overtake_dto = api.model(
    "DocumentOvertake",
    {
        "document_edit_id": fields.Integer(required=True, min=1),
    },
)

team_user_output_list_dto = api.model(
    "TeamUserListOutput",
    {
        "teams": fields.List(fields.Nested(team_user_output_dto)),
    },
)

document_edit_output_dto = api.model(
    "DocumentEditOutput",
    {
        "id": fields.Integer,
        "schema_id": fields.Integer,
        "document_id": fields.Integer,
        "mention_model_id": fields.Integer,
        "entity_model_id": fields.Integer,
        "relation_model_id": fields.Integer,
        "state": fields.Nested(document_edit_state_dto),
    },
)

project_output_dto = api.model(
    "ProjectOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "creator": fields.Nested(user_output_dto),
        "team": fields.Nested(team_dto),
        "schema": fields.Nested(schema_dto),
    },
)

project_user_output_list_dto = api.model(
    "project_user_output_list_dto",
    {
        "projects": fields.List(fields.Nested(project_output_dto)),
    },
)

signup_input_dto = api.model(
    "SignupInput",
    {
        "username": fields.String(
            required=True, description="Username of the new user"
        ),
        "email": fields.String(required=True, description="Email of the new user"),
        "password": fields.String(
            required=True, description="Password for the new user"
        ),
    },
)

user_update_input_dto = api.model(
    "UserUpdateInput",
    {
        "username": fields.String(description="Username of the new user"),
        "email": fields.String(description="Email of the new user"),
        "password": fields.String(description="Password for the new user"),
    },
)

signup_output_dto = api.model(
    "SignupOutput",
    {
        "message": fields.String,
    },
)

login_input_dto = api.model(
    "LoginInput",
    {
        "email": fields.String(required=True, description="The email of the user"),
        "password": fields.String(
            required=True, description="The password of the user"
        ),
    },
)

login_output_dto = api.model(
    "LoginOutput",
    {
        "token": fields.String(
            required=True, description="The JWT token for authenticated user"
        ),
    },
)

mention_update_input_dto = api.model(
    "UpdateMentionInput",
    {
        "schema_mention_id": fields.Integer,
        "token_ids": fields.List(fields.Integer),
        "entity_id": fields.Integer,
    },
)

document_edit_output_soft_delete_dto = api.model(
    "DeleteDocumentEditOutput",
    {
        "message": fields.String,
    },
)

document_delete_output_dto = api.model(
    "DeleteDocumentOutput",
    {
        "message": fields.String,
    },
)

project_delete_output_model = api.model(
    "DeleteProjectOutput",
    {
        "message": fields.String,
    },
)

team_delete_output_model = api.model(
    "DeleteTeamOutput",
    {
        "message": fields.String,
    },
)

relation_update_input_dto = api.model(
    "UpdateRelationInput",
    {
        "schema_relation_id": fields.Integer,
        "mention_head_id": fields.Integer,
        "mention_tail_id": fields.Integer,
    },
)

token_model = api.model(
    "Token",
    {
        "id": fields.Integer(description="Token ID"),
        "text": fields.String(description="Token text"),
        "document_index": fields.Integer(
            description="Index of the token in the document"
        ),
        "sentence_index": fields.Integer(
            description="Index of the token in the sentence"
        ),
        "pos_tag": fields.String(description="Part-of-speech tag"),
    },
)

token_output_list_dto = api.model(
    "TokenListOutput",
    {
        "tokens": fields.List(fields.Nested(token_model)),
    },
)

document_model = api.model(
    "Document",
    {
        "id": fields.Integer(description="Document ID"),
        "tokens": fields.List(
            fields.Nested(token_model), description="List of tokens in the document"
        ),
    },
)

mention_output_dto = api.model(
    "Mention",
    {
        "id": fields.Integer(description="Mention ID"),
        "tag": fields.String(description="Mention tag"),
        "isShownRecommendation": fields.Boolean(
            description="Whether the mention is shown as a recommendation"
        ),
        "document_edit_id": fields.Integer(description="Document Edit ID"),
        "document_recommendation_id": fields.Integer(
            description="Document Recommendation ID", nullable=True
        ),
        "entity_id": fields.Integer(
            description="Entity ID associated with the mention"
        ),
        "tokens": fields.List(
            fields.Nested(token_model),
            description="List of tokens associated with the mention",
        ),
        "schema_mention": fields.Nested(
            schema_mention_output_dto, description="Details of the schema mention"
        ),
    },
)

mention_output_list_dto = api.model(
    "MentionOutputList",
    {
        "mentions": fields.List(
            fields.Nested(mention_output_dto), description="List of mentions"
        ),
    },
)

entity_output_dto = api.model(
    "EntityOutput",
    {
        "id": fields.Integer,
        "isShownRecommendation": fields.Boolean,
        "document_edit_id": fields.Integer,
        "document_recommendation_id": fields.Integer,
        "mentions": fields.List(fields.Nested(mention_output_dto)),
    },
)

entity_output_list_dto = api.model(
    "EntityOutputList",
    {
        "entities": fields.List(fields.Nested(entity_output_dto)),
    },
)

schema_relation_model = api.model(
    "SchemaRelation",
    {
        "id": fields.Integer(description="Schema Relation ID"),
        "tag": fields.String(description="Schema Relation Tag"),
        "description": fields.String(description="Description of the schema relation"),
        "schema_id": fields.Integer(description="Schema ID"),
    },
)

relation_output_model = api.model(
    "RelationOutput",
    {
        "id": fields.Integer(description="Relation ID"),
        "isDirected": fields.Boolean(description="Whether the relation is directed"),
        "isShownRecommendation": fields.Boolean(
            description="Whether the relation is shown as a recommendation"
        ),
        "document_edit_id": fields.Integer(description="Document Edit ID"),
        "document_recommendation_id": fields.Integer(
            description="Document Recommendation ID", nullable=True
        ),
        "schema_relation": fields.Nested(
            schema_relation_model, description="Schema relation details"
        ),
        "tag": fields.String(description="Relation tag"),
        "head_mention": fields.Nested(
            mention_output_dto, description="Head mention of the relation"
        ),
        "tail_mention": fields.Nested(
            mention_output_dto, description="Tail mention of the relation"
        ),
    },
)

relation_output_list_dto = api.model(
    "RelationsOutput",
    {
        "relations": fields.List(
            fields.Nested(relation_output_model), description="List of relations"
        ),
    },
)

finished_document_edit_output_dto = api.model(
    "FinishedDocumentEditOutput",
    {
        "document": fields.Nested(document_model, description="Document details"),
        "mentions": fields.List(
            fields.Nested(mention_output_dto),
            description="List of mentions in the document edit",
        ),
        "relations": fields.List(
            fields.Nested(relation_output_model),
            description="List of relations in the document edit",
        ),
        "schema_id": fields.Integer(description="Schema ID"),
        "state": fields.Nested(document_edit_state_dto),
    },
)

heatmap_output_dto = api.model(
    "HeatmapOutput",
    {
        "id": fields.Integer(description="Token ID"),
        "text": fields.String(description="Token text"),
        "document_index": fields.Integer(
            description="Index of the token in the document"
        ),
        "sentence_index": fields.Integer(
            description="Index of the token in the sentence"
        ),
        "pos_tag": fields.String(description="Part-of-speech tag"),
        "score": fields.Float(description="Score associated with the token"),
    },
)

heat_user_dto = api.model(
    "User",
    {
        "id": fields.Integer(description="User ID"),
        "email": fields.String(description="User email"),
        "username": fields.String(description="User username"),
    },
)

# Define a DocumentEdit DTO
heat_document_edit_dto = api.model(
    "DocumentEdit",
    {
        "id": fields.Integer(description="DocumentEdit ID"),
        "user": fields.Nested(
            heat_user_dto, description="Details of the user who edited the document"
        ),
    },
)

# Define a Document DTO
heat_document_dto = api.model(
    "Document",
    {
        "id": fields.Integer(description="Document ID"),
        "name": fields.String(description="Document name"),
    },
)

# Extend HeatmapOutputList DTO to include document and document_edits
heatmap_output_list_dto = api.model(
    "HeatmapOutputList",
    {
        "items": fields.List(
            fields.Nested(heatmap_output_dto),
            description="List of heatmap token objects",
        ),
        "document": fields.Nested(
            heat_document_dto, description="Details of the document"
        ),
        "document_edits": fields.List(
            fields.Nested(heat_document_edit_dto),
            description="List of document edits with user details",
        ),
    },
)

model_train_input = api.model(
    "ModelTrainInput",
    {
        "model_name": fields.String(description="Name of trained model", required=True),
        "model_type": fields.String(description="Type of trained model", required=True),
        "model_step": fields.String(
            description="Steps this model can be used for, valid steps: mention, entity, relation",
            required=True,
        ),
        "document_edits": fields.List(
            fields.Integer(required=True),
            required=True,
            description="IDs of document edits to consider for training",
        ),
        "settings": fields.List(fields.Nested(recommendation_model_settings_dto)),
    },
)

model_train_output = api.model(
    "ModelTrainOutput",
    {
        "id": fields.Integer(),
        "name": fields.String(description="Name of trained model"),
        "type": fields.String(description="Type of trained model"),
        "step": fields.Nested(model_step_dto),
        "schema_id": fields.Integer(description="Schema ID"),
    },
)

model_train_output_list_dto = api.model(
    "ModelTrainOutputList", {"models": fields.List(fields.Nested(model_train_output))}
)

recommendation_model_settings_output_dto = api.model(
    "RecommendationModelParameterOutput",
    {
        "id": fields.Integer,
        "key": fields.String,
        "value": fields.String,
    },
)

document_edit_model_output_dto = api.model(
    "DocumentEditModelOutput",
    {
        "id": fields.Integer(description="ID"),
        "document_edit_id": fields.Integer(description="Document Edit ID"),
        "name": fields.String(description="Name of trained model"),
        "type": fields.String(description="Type of trained model"),
        "step": fields.Nested(model_step_dto),
        "settings": fields.List(
            fields.Nested(recommendation_model_settings_output_dto)
        ),
    },
)

document_edit_model_output_list_dto = api.model(
    "DocumentEditModelOutputList",
    {
        "models": fields.List(fields.Nested(document_edit_model_output_dto)),
    },
)

model_type_with_settings = api.model(
    "ModelTypeWithSettings",
    {
        "model_type": fields.String(required=True),
        "name": fields.String(
            description="Name of trained model (in human understandable format)"
        ),
        "id": fields.Integer(
            description="Id of the related RecommendationModel in the database that is connected to the given schema"
        ),
        "settings": fields.Raw(
            required=False,
            description="""
Dictionary of key value pairs, that can be added as query param to the _model_type_.
_Keys_ are always of type string.
_Values_ are of type object containing the following keys:
- **values** => possible values for the key
    - if the value is an array, all values of the array are valid (enum like behavior)
    - if the value is an string, the possible type is the value of the string
        - _"string"_ => any string can be an input
        - _"integer"_ => any integer can be an input
- **default** => the default value for the key. _Null_ if there is no default value      
                        """,
        ),
    },
)

train_models_with_settings = api.model(
    "TrainModelsWithSettings",
    {
        "model_type": fields.String(required=True),
        "settings": fields.Raw(
            required=False,
            description="""
Dictionary of key value pairs, that can be added as query param to the _model_type_.
_Keys_ are always of type string.
_Values_ are of type object containing the following keys:
- **values** => possible values for the key
    - if the value is an array, all values of the array are valid (enum like behavior)
    - if the value is an string, the possible type is the value of the string
        - _"string"_ => any string can be an input
        - _"integer"_ => any integer can be an input
- **default** => the default value for the key. _Null_ if there is no default value      
                        """,
        ),
    },
)

get_recommendation_models_output_dto = api.model(
    "GetRecommendationModelsOutput",
    {
        "mention": fields.List(fields.Nested(model_type_with_settings)),
        "entity": fields.List(fields.Nested(model_type_with_settings)),
        "relation": fields.List(fields.Nested(model_type_with_settings)),
    },
)

get_train_models_output_dto = api.model(
    "GetTrainModelsOutput",
    {
        "mention": fields.List(fields.Nested(train_models_with_settings)),
        "entity": fields.List(fields.Nested(train_models_with_settings)),
        "relation": fields.List(fields.Nested(train_models_with_settings)),
    },
)

jaccard_index_response = api.model(
    "jaccard index response",
    {
        "combined_index": fields.Float(
            required=True,
            description="An approximation of the overall Jaccard index, where relations and entities are weighted less than mentions.",
        ),
        "mention_index": fields.Float(required=True),
        "relation_index": fields.Float(required=True),
        "considered_relation_index": fields.Float(required=True),
        "entity_index": fields.Float(required=True),
        "considered_entities_index": fields.Float(required=True),
    },
)

jaccard_response = api.model(
    "jaccard index response",
    {
        "average": fields.Nested(
            jaccard_index_response,
            description="The average jaccard index where the index for all pairs of documents is calculated and the average is returned, e.g. ((A∩B/A∪B)+(A∩C/A∪C)+(B∩C/B∪C))/3",
        ),
        "combined": fields.Nested(
            jaccard_index_response,
            description="The combined jaccard index where one index for all documents in calculated at once, e.g. (A∩B∩C/A∪B∪C)",
        ),
    },
)

jaccard_output_dto = api.model(
    "JaccardOutput",
    {
        "result": fields.List(
            fields.Nested(jaccard_response),
            description="Result of Jaccard calculation",
        ),
        "document": fields.Nested(
            heat_document_dto, description="Details of the document"
        ),
        "document_edits": fields.List(
            fields.Nested(heat_document_edit_dto),
            description="List of document edits with user details",
        ),
    },
)

document_edit_state_input_dto = api.model(
    "DocumentEditStateOutput",
    {
        "state": fields.String(required=True, description="State of the document edit"),
    },
)


document_state_update_dto = api.model(
    "DocumentStateUpdate",
    {
        "state_id": fields.Integer(
            required=True, description="ID of the new document state"
        ),
    },
)

document_edit_schema_output_dto = api.model(
    "DocumentEditSchemaOutput",
    {
        "document": fields.Nested(
            heat_document_dto, description="Details of the document"
        ),
        "id": fields.Integer(description="Document Edit ID"),
        "state": fields.Nested(
            api.model(
                "DocumentEditState",
                {
                    "id": fields.Integer,
                    "type": fields.String,
                },
            )
        ),
        "user": fields.Nested(user_output_dto),
    },
)

f1_score_dto = api.model(
    "F1Score",
    {
        "mention_score": fields.Integer(description="Mention Score"),
        "considered_entity_quote": fields.Integer(
            description="Considered Entity Quote"
        ),
        "entity_score": fields.Integer(description="Entity Score"),
        "considered_relation_quote": fields.Integer(
            description="Considered Relation Quote"
        ),
        "relation_score": fields.Integer(description="Relation Score"),
    },
)


document_import_dto = api.model(
    "DocumentImportList", {"documents": fields.List(fields.Raw())}
)

scope_create_input_dto = api.model(
    "ScopeCreateInput",
    {
        "schema_scope_id": fields.Integer(required=True),
        "token_start_id": fields.Integer(required=True),
        "token_end_id": fields.Integer(required=True),
        "parent_scope_id": fields.Integer(required=False),
    },
)

schema_scope_output_dto = api.model(
    "SchemaScopeOutput",
    {
        "id": fields.Integer(),
        "type": fields.String(),
        "description": fields.String(),
        "schema_id": fields.Integer(),
        "color": fields.String(),
    },
)

scope_output_dto = api.model(
    "ScopeOutput",
    {
        "id": fields.Integer(),
        "schema_scope": fields.Nested(schema_scope_output_dto),
        "document_edit_id": fields.Integer(),
        "document_recommendation_id": fields.Integer(),
        "token_start": fields.Nested(token_model),
        "token_end": fields.Nested(token_model),
        "parent_scope_id": fields.Integer(),
    },
)
scope_output_dto["children"] = fields.List(fields.Nested(scope_output_dto))

scope_similarity_single_scope = api.model(
    "ScopeSimilaritySingleScope",
    {
        "token_start": fields.Nested(token_model),
        "token_end": fields.Nested(token_model),
        "similarity": fields.Float(),
    },
)

scope_similarity_output_dto = api.model(
    "ScopeSimilarityOutput",
    {
        "total_similarity": fields.Float(),
        "#reference_scopes": fields.Integer(),
        "#comparison_scopes": fields.Integer(),
        "similarity_per_scope": fields.List(
            fields.Nested(scope_similarity_single_scope)
        ),
    },
)


scope_flat_output_dto = api.model(
    "ScopeFlatOutput",
    {
        "id": fields.Integer(),
        "scope_type": fields.String(),
        "document_edit_id": fields.Integer(),
        "document_recommendation_id": fields.Integer(),
        "startTokenDocumentIndex": fields.Integer(),
        "endTokenDocumentIndex": fields.Integer,
        "parent_scope_id": fields.Integer(),
    },
)
