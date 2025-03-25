from flask_restx import fields
from app.extension import api

schema_id = api.model("SchemaId", {"id": fields.Integer(description="Schema ID")})
document_id = api.model("DocumentId", {"id": fields.Integer(description="Document ID")})
document_edit_id = api.model(
    "DocumentEditId", {"id": fields.Integer(description="DocumentEdit ID")}
)
document_recommendation_id = api.model(
    "DocumentRecommendationId",
    {"id": fields.Integer(description="Document Recommendation ID")},
)
entity_id = api.model("EntityId", {"id": fields.Integer(description="Entity ID")})
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
        "team": fields.Nested(
            api.model("TeamId", {"id": fields.Integer(required=True, min=1)})
        ),
        "schema": fields.Nested(
            api.model("SchemaId", {"id": fields.Integer(required=True, min=1)})
        ),
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
        "schema": fields.Nested(
            api.model(
                "Schema",
                {
                    "id": fields.Integer,
                    "name": fields.String,
                },
            )
        ),
    },
)

document_state_dto = api.model(
    "DocumentState",
    {
        "id": fields.Integer,
        "type": fields.String,
    },
)


document_edit_state_dto = api.model(
    "DocumentEditState",
    {
        "id": fields.Integer,
        "type": fields.String,
    },
)

document_edit_output_2_dto = api.model(
    "DocumentEditOutput2",
    {
        "id": fields.Integer(required=True),
        "state": fields.Nested(document_edit_state_dto),
        "user": fields.Nested(user_output_dto),
    },
)

document_output_dto = api.model(
    "DocumentList",
    {
        "id": fields.Integer,
        "content": fields.String,
        "name": fields.String,
        "state": fields.Nested(document_state_dto),
        "project": fields.Nested(project_dto),
        "team": fields.Nested(team_dto),
        "creator": fields.Nested(user_output_dto),
        "documentEdits": fields.List(fields.Nested(document_edit_output_2_dto)),
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

team_output_dto = api.model(
    "TeamUserOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "creator": fields.Nested(user_output_dto),
        "members": fields.List(fields.Nested(user_output_dto)),
    },
)

schema_constraint_output_dto = api.model(
    "SchemaConstraintOutput",
    {
        "id": fields.Integer,
        "isDirected": fields.Boolean,
        "schemaRelation": fields.Nested(schema_relation_output_dto),
        "schemaHeadMention": fields.Nested(schema_mention_output_dto),
        "schemaTailMention": fields.Nested(schema_mention_output_dto),
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

small_schema_output_dto = api.model(
    "SmallSchemaOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "isFixed": fields.Boolean,
        "modellingLanguage": fields.Nested(
            api.model(
                "ModellingLanguage",
                {
                    "id": fields.Integer,
                    "type": fields.String,
                },
            ),
        ),
        "team": fields.Nested(team_output_dto),
    },
)

schema_output_dto = api.model(
    "SchemaOutput",
    {
        "id": fields.Integer,
        "name": fields.String,
        "isFixed": fields.Boolean,
        "modellingLanguage": fields.Nested(
            api.model(
                "ModellingLanguage",
                {
                    "id": fields.Integer,
                    "type": fields.String,
                },
            ),
        ),
        "team": fields.Nested(team_output_dto),
        "models": fields.List(fields.Nested(schema_model_dto), required=False),
        "schemaMentions": fields.List(fields.Nested(schema_mention_output_dto)),
        "schemaRelations": fields.List(fields.Nested(schema_relation_output_dto)),
        "schemaConstraints": fields.List(fields.Nested(schema_constraint_output_dto)),
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
        "teams": fields.List(fields.Nested(team_output_dto)),
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
        "team": fields.Nested(team_output_dto),
        "schema": fields.Nested(small_schema_output_dto),
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
        "jwt": fields.String(
            required=True, description="The JWT token for authenticated user"
        ),
        "user": fields.Nested(user_output_dto),
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
        "documentIndex": fields.Integer(
            description="Index of the token in the document"
        ),
        "sentenceIndex": fields.Integer(
            description="Index of the token in the sentence"
        ),
        "posTag": fields.String(description="Part-of-speech tag"),
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
        "content": fields.String(description="Document content"),
        "creator": fields.Nested(user_output_dto),
        "name": fields.String(description="Document name"),
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
        "documentEdit": fields.Nested(document_edit_id),
        "documentRecommendation": fields.Nested(document_recommendation_id),
        "entity": fields.Nested(entity_id),
        "tokens": fields.List(
            fields.Nested(token_model),
            description="List of tokens associated with the mention",
        ),
        "schemaMention": fields.Nested(
            schema_mention_output_dto, description="Details of the schema mention"
        ),
    },
)

entity_output_dto = api.model(
    "EntityOutput",
    {
        "id": fields.Integer,
        "isShownRecommendation": fields.Boolean,
        "documentEdit": fields.Nested(document_edit_id),
        "documentRecommendation": fields.Nested(document_recommendation_id),
        "mentions": fields.List(fields.Nested(mention_output_dto)),
    },
)

schema_relation_model = api.model(
    "SchemaRelation",
    {
        "id": fields.Integer(description="Schema Relation ID"),
        "tag": fields.String(description="Schema Relation Tag"),
        "description": fields.String(description="Description of the schema relation"),
        "schema": fields.Nested(schema_id),
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
        "documentEdit": fields.Nested(document_edit_id),
        "documentRecommendation": fields.Nested(document_recommendation_id),
        "schemaRelation": fields.Nested(
            schema_relation_model, description="Schema relation details"
        ),
        "tag": fields.String(description="Relation tag"),
        "headMention": fields.Nested(
            mention_output_dto, description="Head mention of the relation"
        ),
        "tailMention": fields.Nested(
            mention_output_dto, description="Tail mention of the relation"
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
        "schema": fields.Nested(schema_dto),
        "state": fields.Nested(document_edit_state_dto),
    },
)

heatmap_output_dto = api.model(
    "HeatmapOutput",
    {
        "id": fields.Integer(description="Token ID"),
        "text": fields.String(description="Token text"),
        "documentIndex": fields.Integer(
            description="Index of the token in the document"
        ),
        "sentenceIndex": fields.Integer(
            description="Index of the token in the sentence"
        ),
        "posTag": fields.String(description="Part-of-speech tag"),
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
