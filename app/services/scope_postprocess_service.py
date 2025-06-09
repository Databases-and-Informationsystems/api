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
        violation_counter = _ViolationCounter()

        violation_counter.total_scopes = len(scope_recommendations)

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

        violation_counter._count_scope_tree_violations(
            scope_recommendations,
            schema_scope_dict,
            schema_scope_constraint_dict,
            token_index_dict,
        )

        scope_recommendations = self.__add_root(scope_recommendations, len(tokens) - 1)

        scope_recommendations = self.__fix_tree_position(
            scope_recommendations, schema_scope_dict
        )

        scope_recommendations, _ = self.extend_child_scopes(scope_recommendations)

        scope_recommendations = self.__move_up_incorrect_scopes(
            scope_recommendations, schema_scope_constraint_dict, schema_scope_dict
        )

        merged_scopes = self.__merge_consecutive_scopes(
            scope_recommendations,
            token_index_dict,
            schema_scope_dict,
        )
        merged_scopes = self.__replace_scopes_with_missing_children(
            merged_scopes, schema_scope_dict
        )
        merged_scopes = self.__move_up_bottom_scopes(merged_scopes, schema_scope_dict)

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
                x["id"],
            ),
        )
        logging.info(merged_scopes)
        violation_counter.total_scopes_postprocessed = len(merged_scopes)

        violation_counter._log_concept_violations()

        return merged_scopes

    def __add_root(self, scope_recommendations, max_token):
        for scope in scope_recommendations:
            if scope["endTokenDocumentIndex"] > max_token:
                scope["endTokenDocumentIndex"] = max_token
            if scope["scope_type"] == "root":
                scope["parent_scope_id"] = None
                return scope_recommendations
        root = {
            "parent_scope_id": None,
            "startTokenDocumentIndex": 0,
            "endTokenDocumentIndex": max_token,
            "id": 1000 + len(scope_recommendations),
            "scope_type": "root",
        }
        for scope in scope_recommendations:
            if scope["parent_scope_id"] is None or scope["parent_scope_id"] == -1:
                scope["parent_scope_id"] = root["id"]
        scope_recommendations.append(root)
        return scope_recommendations

    def __fix_tree_position(self, scope_recommendations, schema_scope_dict):
        # Rule: Reorder tree, so that possible parent with the closest token range is chosen as parent
        for scope in scope_recommendations:
            best_parent = _find_best_parent(
                scope, scope_recommendations, schema_scope_dict
            )
            if best_parent and scope.get("parent_scope_id") != best_parent["id"]:
                scope["parent_scope_id"] = best_parent["id"]

        return scope_recommendations

    def extend_child_scopes(self, scope_recommendations):
        scope_violations = 0
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
            if (
                recommendation_id_dict[first_child["id"]]["startTokenDocumentIndex"]
                < parent["startTokenDocumentIndex"]
            ) or (
                recommendation_id_dict[last_child["id"]]["endTokenDocumentIndex"]
                > parent["endTokenDocumentIndex"]
            ):
                scope_violations += 1
                recommendation_id_dict[first_child["id"]]["startTokenDocumentIndex"] = (
                    parent["startTokenDocumentIndex"]
                )
                recommendation_id_dict[last_child["id"]]["endTokenDocumentIndex"] = (
                    parent["endTokenDocumentIndex"]
                )

            for i, child in enumerate(parent_children_dict[key][1:]):
                if (
                    recommendation_id_dict[child["id"]]["startTokenDocumentIndex"]
                    != parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                ):
                    recommendation_id_dict[child["id"]]["startTokenDocumentIndex"] = (
                        parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                    )
                    scope_violations += 1

        return recommendation_id_dict.values(), scope_violations

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


class _ViolationCounter:
    max_token_exceeded = 0
    root_missing = False
    first_child_later_start = 0
    last_child_earlier_end = 0
    gaps_in_between = 0
    child_exceeding_parent = 0
    horizontal_unmerged = 0
    vertical_unmerged = 0
    parent_child_forbidden = 0
    too_many_children = 0
    too_few_children = 0
    scope_overlapping = 0
    wrong_tree_position = 0
    total_scopes = 0
    total_scopes_postprocessed = 0

    def _log_concept_violations(self):
        log_message = f"""
            Structural Scope Tree Violations:
            - max_token_exceeded: {self.max_token_exceeded}
            - root_missing: {self.root_missing}
            - first_child_later_start: {self.first_child_later_start}
            - last_child_earlier_end: {self.last_child_earlier_end}
            - gaps_in_between: {self.gaps_in_between}
            - child_exceeding_parent: {self.child_exceeding_parent} 
            - parent_child_forbidden: {self.parent_child_forbidden}
            - too_many_children: {self.too_many_children}
            - too_few_children: {self.too_few_children}
            - scope_overlapping: {self.scope_overlapping}
            - wrong_tree_position: {self.wrong_tree_position}

            Semantic Scope Tree Violations:
            - horizontal_unmerged: {self.horizontal_unmerged}
            - vertical_unmerged: {self.vertical_unmerged}

            Scopes:
            - total_scopes: {self.total_scopes}
            - total_scopes_postprocessed: {self.total_scopes_postprocessed}
            """
        logging.info(log_message)

    def _count_scope_tree_violations(
        self,
        scope_recommendations,
        schema_scope_dict,
        schema_scope_constraint_dict,
        token_index_dict,
    ):
        parent_children_dict = {
            scope_recommendation["id"]: []
            for scope_recommendation in scope_recommendations
        }

        for scope_recommendation in scope_recommendations:
            if (
                scope_recommendation["parent_scope_id"] is not None
                and scope_recommendation["parent_scope_id"] >= 0
            ):
                parent_children_dict[scope_recommendation["parent_scope_id"]].append(
                    scope_recommendation
                )

        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        parent_children_dict = dict(sorted(parent_children_dict.items()))

        # Check if root exists
        self.root_missing = True
        for scope in scope_recommendations:
            if scope["scope_type"] == "root":
                self.root_missing = False
                break

        # Check if max token is exceeded
        for scope in scope_recommendations:
            if scope["endTokenDocumentIndex"] >= len(token_index_dict):
                self.max_token_exceeded += 1

        # Count how often scope is at wrong position in tree
        for scope in scope_recommendations:
            best_parent = _find_best_parent(
                scope, scope_recommendations, schema_scope_dict
            )
            if best_parent and scope.get("parent_scope_id") != best_parent["id"]:
                self.wrong_tree_position += 1

        # Count gaps in between, at the beginning and at the end of a subtree
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
            if (
                recommendation_id_dict[first_child["id"]]["startTokenDocumentIndex"]
                < parent["startTokenDocumentIndex"]
            ) or (
                recommendation_id_dict[last_child["id"]]["endTokenDocumentIndex"]
                > parent["endTokenDocumentIndex"]
            ):
                self.child_exceeding_parent += 1

            if (
                recommendation_id_dict[first_child["id"]]["startTokenDocumentIndex"]
                > parent["startTokenDocumentIndex"]
            ):
                self.first_child_later_start += 1
            if (
                recommendation_id_dict[last_child["id"]]["endTokenDocumentIndex"]
                < parent["endTokenDocumentIndex"]
            ):
                self.last_child_earlier_end += 1
            for i, child in enumerate(parent_children_dict[key][1:]):
                if (
                    recommendation_id_dict[child["id"]]["startTokenDocumentIndex"]
                    != parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                ):
                    if (
                        recommendation_id_dict[child["id"]]["startTokenDocumentIndex"]
                        > parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                    ):
                        self.gaps_in_between += 1
                    else:
                        self.scope_overlapping += 1

        for key in parent_children_dict:
            if len(parent_children_dict[key]) <= 1:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["startTokenDocumentIndex"],
            )

            for i, scope in enumerate(parent_children_dict[key][1:]):
                if (
                    schema_scope_dict[scope["scope_type"]]["horizontal_merging"]
                    and scope["scope_type"]
                    == parent_children_dict[key][i]["scope_type"]
                    and scope["startTokenDocumentIndex"]
                    == parent_children_dict[key][i]["endTokenDocumentIndex"] + 1
                ):
                    self.horizontal_unmerged += 1

        for key in list(parent_children_dict.keys()):
            if len(parent_children_dict[key]) == 0 or key is None:
                continue

            parent = recommendation_id_dict[key]
            for child in parent_children_dict[key]:

                if (
                    schema_scope_dict[parent["scope_type"]]["vertical_merging"]
                    and parent["scope_type"] == child["scope_type"]
                ):
                    self.vertical_unmerged += 1
                elif not schema_scope_constraint_dict.get(
                    (parent["scope_type"], child["scope_type"])
                ):
                    if (
                        parent["scope_type"] == "root"
                        and child["scope_type"] == "sequential"
                    ):
                        self.vertical_unmerged += 1
                    else:
                        self.parent_child_forbidden += 1
        for key in parent_children_dict.keys():
            if len(parent_children_dict[key]) == 0 or key is None:
                continue
            count_procedural_children = 0
            for child in parent_children_dict[key]:
                if schema_scope_dict[child["scope_type"]]["process_relevant"]:
                    count_procedural_children += 1
            parent = recommendation_id_dict[key]
            if (
                schema_scope_dict[parent["scope_type"]][
                    "minimum_children_process_relevant"
                ]
                > count_procedural_children
            ):
                self.too_few_children += 1
            elif (
                schema_scope_dict[parent["scope_type"]][
                    "maximum_children_process_relevant"
                ]
                is not None
                and count_procedural_children
                > schema_scope_dict[parent["scope_type"]][
                    "maximum_children_process_relevant"
                ]
            ):
                self.too_many_children += 1

        return recommendation_id_dict.values()


def _find_best_parent(scope, scope_recommendations, schema_scope_dict):
    best_parent = None
    parent = None
    for scope_rec in scope_recommendations:
        if scope["parent_scope_id"] == scope_rec["id"]:
            parent = scope_rec
    if parent is not None and (
        parent["startTokenDocumentIndex"] >= scope["startTokenDocumentIndex"]
        or parent["endTokenDocumentIndex"] <= scope["endTokenDocumentIndex"]
    ):
        # Child exceeding parent => other violation
        return None
    for possible_parent in scope_recommendations:
        if (
            possible_parent["id"] == scope["id"]
            or schema_scope_dict[possible_parent["scope_type"]].get(
                "maximum_children_process_relevant"
            )
            == 0
        ):
            continue

        if (
            possible_parent["startTokenDocumentIndex"]
            <= scope["startTokenDocumentIndex"]
            and possible_parent["endTokenDocumentIndex"]
            >= scope["endTokenDocumentIndex"]
        ):

            if not best_parent or (
                (
                    possible_parent["endTokenDocumentIndex"]
                    - possible_parent["startTokenDocumentIndex"]
                )
                < (
                    best_parent["endTokenDocumentIndex"]
                    - best_parent["startTokenDocumentIndex"]
                )
            ):
                best_parent = possible_parent
    return best_parent


scope_postprocess_service = ScopePostprocessService()
