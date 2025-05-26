import logging
from collections import defaultdict


class ScopePostprocessService:

    def postprocess_scope_tree(
        self,
        scope_recommendations,
        tokens,
        schema_scopes,
        schema_scope_constraints,
    ):
        schema_scope_dict = dict()
        for schema_scope in schema_scopes:
            schema_scope_dict[schema_scope["type"]] = schema_scope

        token_index_dict = dict()
        for token in tokens:
            token_index_dict[token["document_index"]] = token["id"]

        schema_scope_constraint_dict = dict()
        for schema_scope_constraint in schema_scope_constraints:
            schema_scope_constraint_dict[
                (
                    schema_scope_constraint["parent_type"]["type"],
                    schema_scope_constraint["child_type"]["type"],
                )
            ] = True
        scope_recommendations = self.extend_child_scopes(scope_recommendations)

        scope_recommendations = self.__move_up_incorrect_scopes(
            scope_recommendations, schema_scope_constraint_dict, schema_scope_dict
        )
        scope_recommendations = self.__move_up_bottom_scopes(
            scope_recommendations, schema_scope_dict
        )

        merged_scopes = self.__merge_consecutive_scopes(
            scope_recommendations,
            token_index_dict,
            schema_scope_dict,
        )
        merged_scopes = self.__replace_scopes_with_missing_children(
            merged_scopes, schema_scope_dict
        )

        merged_scopes = self.__merge_consecutive_scopes(
            merged_scopes,
            token_index_dict,
            schema_scope_dict,
        )

        merged_scopes = self.__merge_equal_scopes(merged_scopes)
        merged_scopes = sorted(
            merged_scopes,
            key=lambda x: (
                x["startTokenDocumentIndex"],
                -x["endTokenDocumentIndex"],
                x["parent_scope_id"],
            ),
        )
        logging.info(merged_scopes)
        return merged_scopes

    def extend_child_scopes(self, scope_recommendations):
        # Rule: All tokens have to be covered on leaf level
        parent_children_dict = {
            scope_recommendation["id"]: []
            for scope_recommendation in scope_recommendations
        }
        for scope_recommendation in scope_recommendations:
            if scope_recommendation["parent_scope_id"]:
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )

        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        parent_children_dict = dict(sorted(parent_children_dict.items()))
        for key in parent_children_dict:
            if len(parent_children_dict[key]) == 0 or key is None:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["startTokenDocumentIndex"],
            )
            parent = recommendation_id_dict[key]
            first_child = parent_children_dict[key][0]
            last_child = parent_children_dict[key][-1]

            recommendation_id_dict[first_child["id"]]["startTokenDocumentIndex"] = (
                parent["startTokenDocumentIndex"]
            )
            recommendation_id_dict[last_child["id"]]["endTokenDocumentIndex"] = parent[
                "endTokenDocumentIndex"
            ]
            for i, child in enumerate(parent_children_dict[key][1:]):
                recommendation_id_dict[child["id"]]["startTokenDocumentIndex"] = (
                    parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                )
        return recommendation_id_dict.values()

    def __merge_consecutive_scopes(
        self,
        scope_recommendations,
        token_index_dict,
        schema_scope_dict,
    ):
        # Rule: merge scopes, when horizontal merging is allowed
        merged_scopes = []

        merged_scope_id_mapping = dict()
        parent_children_dict = {
            scope_recommendation["id"]: []
            for scope_recommendation in scope_recommendations
        }
        parent_children_dict[None] = []

        for scope_recommendation in scope_recommendations:
            parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                scope_recommendation
            )

        for key in parent_children_dict:
            if len(parent_children_dict[key]) == 0:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["startTokenDocumentIndex"],
            )
            merged = parent_children_dict[key][0]
            merged_scope_id_mapping[merged["id"]] = merged["id"]

            if len(parent_children_dict[key]) == 1:
                merged_scopes.append(merged)
            else:
                for scope in parent_children_dict[key][1:]:
                    if (
                        schema_scope_dict[scope["scope_type"]]["horizontal_merging"]
                        and scope["scope_type"] == merged["scope_type"]
                        and scope["startTokenDocumentIndex"]
                        == merged["endTokenDocumentIndex"] + 1
                    ):
                        merged_scope_id_mapping[scope["id"]] = merged["id"]
                        for s in parent_children_dict[scope["id"]]:
                            parent_children_dict[merged["id"]].append(s)
                        parent_children_dict[scope["id"]] = []
                        merged = {
                            "id": merged["id"],
                            "scope_type": merged["scope_type"],
                            "startTokenDocumentIndex": merged[
                                "startTokenDocumentIndex"
                            ],
                            "endTokenDocumentIndex": scope["endTokenDocumentIndex"],
                            "parent_scope_id": merged["parent_scope_id"],
                        }
                    else:
                        merged_scopes.append(merged)
                        merged = scope
                        merged_scope_id_mapping[merged["id"]] = merged["id"]

                merged_scopes.append(merged)
        for merged_scope in merged_scopes:
            merged_scope["id"] = merged_scope_id_mapping[merged_scope["id"]]
            merged_scope["parent_scope_id"] = merged_scope_id_mapping.get(
                merged_scope["parent_scope_id"]
            )
            merged_scope["schema_scope_id"] = schema_scope_dict[
                merged_scope["scope_type"]
            ]["id"]
            merged_scope["token_start_id"] = token_index_dict[
                merged_scope["startTokenDocumentIndex"]
            ]
            merged_scope["token_end_id"] = token_index_dict[
                merged_scope["endTokenDocumentIndex"]
            ]
        return merged_scopes

    def __move_up_incorrect_scopes(
        self, scope_recommendations, schema_scope_constraint_dict, schema_scope_dict
    ):
        # Rule: replace parent with children if parent-child-relation is not allowed or vertical scope merging is allowed
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        change = True
        while change:
            change = False
            parent_children_dict = {
                scope_recommendation["id"]: []
                for scope_recommendation in recommendation_id_dict.values()
            }
            parent_children_dict[None] = []
            for scope_recommendation in recommendation_id_dict.values():
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )
            for key in list(parent_children_dict.keys()):
                if len(parent_children_dict[key]) == 0 or key is None:
                    continue

                parent = recommendation_id_dict[key]
                for child in parent_children_dict[key]:
                    if (
                        not schema_scope_constraint_dict.get(
                            (parent["scope_type"], child["scope_type"])
                        )
                        or (
                            schema_scope_dict[parent["scope_type"]]["vertical_merging"]
                            and parent["scope_type"] == child["scope_type"]
                        )
                    ) and len(parent_children_dict[child["id"]]) > 0:
                        change = True
                        for child_child in parent_children_dict[child["id"]]:
                            recommendation_id_dict[child_child["id"]][
                                "parent_scope_id"
                            ] = child["parent_scope_id"]
                        if parent_children_dict[child["id"]]:
                            parent_children_dict[child["id"]] = []
                            del recommendation_id_dict[child["id"]]
                if change:
                    break

        return recommendation_id_dict.values()

    def __move_up_bottom_scopes(self, scope_recommendations, schema_scope_dict):
        # Rule: process-irrelevant scopes can be moved up to higher tree-level, if they are the first/last scope inside a parent
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        # first child
        change = True
        while change:
            change = False
            parent_children_dict = {
                scope_recommendation["id"]: []
                for scope_recommendation in recommendation_id_dict.values()
            }
            parent_children_dict[None] = []
            for scope_recommendation in recommendation_id_dict.values():
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )

            for key in list(parent_children_dict.keys()):
                if (
                    len(parent_children_dict[key]) == 0
                    or key is None
                    or recommendation_id_dict[key]["scope_type"] == "root"
                ):
                    continue
                parent_children_dict[key] = sorted(
                    parent_children_dict[key],
                    key=lambda x: x["startTokenDocumentIndex"],
                )
                first_child = parent_children_dict[key][0]
                parent = recommendation_id_dict[key]
                if (
                    not schema_scope_dict[first_child["scope_type"]]["process_relevant"]
                    and first_child["startTokenDocumentIndex"]
                    == recommendation_id_dict[key]["startTokenDocumentIndex"]
                ):
                    change = True
                    if len(parent_children_dict[key]) == 1:  # replace parent with child
                        parent_id = parent["id"]
                        parent_parent_id = parent["parent_scope_id"]
                        recommendation_id_dict[key] = first_child
                        recommendation_id_dict[key]["id"] = parent_id
                        recommendation_id_dict[key][
                            "parent_scope_id"
                        ] = parent_parent_id
                        del recommendation_id_dict[first_child["id"]]
                    else:  # move first child one layer up
                        first_child["parent_scope_id"] = parent["parent_scope_id"]
                        parent["startTokenDocumentIndex"] = (
                            first_child["endTokenDocumentIndex"] + 1
                        )

        # last child
        change = True
        while change:
            change = False
            parent_children_dict = {
                scope_recommendation["id"]: []
                for scope_recommendation in recommendation_id_dict.values()
            }
            parent_children_dict[None] = []
            for scope_recommendation in recommendation_id_dict.values():
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )

            for key in list(parent_children_dict.keys()):
                if (
                    len(parent_children_dict[key]) == 0
                    or key is None
                    or recommendation_id_dict[key]["scope_type"] == "root"
                ):
                    continue
                parent_children_dict[key] = sorted(
                    parent_children_dict[key],
                    key=lambda x: x["startTokenDocumentIndex"],
                )
                last_child = parent_children_dict[key][-1]
                parent = recommendation_id_dict[key]
                if (
                    not schema_scope_dict[last_child["scope_type"]]["process_relevant"]
                    and last_child["endTokenDocumentIndex"]
                    == recommendation_id_dict[key]["endTokenDocumentIndex"]
                ):
                    change = True
                    last_child["parent_scope_id"] = parent["parent_scope_id"]
                    parent["endTokenDocumentIndex"] = (
                        last_child["startTokenDocumentIndex"] - 1
                    )
        return recommendation_id_dict.values()

    def __replace_scopes_with_missing_children(
        self, scope_recommendations, schema_scope_dict
    ):
        # Rule: if a scope has invalid number of children, delete it and replace with the children
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        change = True
        while change:
            change = False
            parent_children_dict = {
                scope_recommendation["id"]: []
                for scope_recommendation in recommendation_id_dict.values()
            }
            parent_children_dict[None] = []
            for scope_recommendation in recommendation_id_dict.values():
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )

            for key in list(parent_children_dict.keys()):
                if len(parent_children_dict[key]) == 0 or key is None:
                    continue
                count_procedural_children = 0
                for child in parent_children_dict[key]:
                    if schema_scope_dict[child["scope_type"]]["process_relevant"]:
                        count_procedural_children += 1

                parent = recommendation_id_dict[key]
                if schema_scope_dict[parent["scope_type"]][
                    "minimum_children_process_relevant"
                ] > count_procedural_children or (
                    schema_scope_dict[parent["scope_type"]][
                        "maximum_children_process_relevant"
                    ]
                    is not None
                    and count_procedural_children
                    > schema_scope_dict[parent["scope_type"]][
                        "maximum_children_process_relevant"
                    ]
                ):
                    change = True
                    for child in parent_children_dict[key]:
                        recommendation_id_dict[child["id"]]["parent_scope_id"] = parent[
                            "parent_scope_id"
                        ]
                    del recommendation_id_dict[key]
                    parent_children_dict[key] = []
        return recommendation_id_dict.values()

    def __merge_equal_scopes(self, merged_scopes):
        # Rule: If two scopes are equal regarding type and token range, merge them
        scope_id_dict = dict()
        parent_children_dict = defaultdict(list)
        for merged_scope in merged_scopes:
            parent_children_dict[merged_scope["parent_scope_id"]].append(merged_scope)
            scope_id_dict[merged_scope["id"]] = merged_scope

        # Merge child with parent if type and bounds are equal
        for key in list(parent_children_dict.keys()):
            if len(parent_children_dict[key]) != 1 or key is None:
                continue
            scope = parent_children_dict[key][0]
            if scope_id_dict[key]["scope_type"] != scope["scope_type"]:
                continue

            if (
                scope_id_dict[key]["startTokenDocumentIndex"]
                == scope["startTokenDocumentIndex"]
                and scope_id_dict[key]["endTokenDocumentIndex"]
                == scope["endTokenDocumentIndex"]
            ):
                for child_scope in parent_children_dict[scope["id"]]:
                    child_scope["parent_scope_id"] = scope["parent_scope_id"]
                merged_scopes = [s for s in merged_scopes if s["id"] != scope["id"]]
        return merged_scopes


scope_postprocess_service = ScopePostprocessService()
