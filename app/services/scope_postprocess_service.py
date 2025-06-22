import logging
from collections import defaultdict

from app.file_logger import logger


class ScopePostprocessService:
    def postprocess_scope_tree(
        self,
        scope_recommendations,
        tokens,
        schema_scopes,
        schema_scope_constraints,
        count_violations=True,
    ):
        violation_counter = _ViolationCounter()
        violation_counter.total_scopes = len(scope_recommendations)

        schema_scope_dict = dict()
        for schema_scope in schema_scopes:
            schema_scope_dict[schema_scope["type"]] = schema_scope

        token_index_dict = dict()
        for token in tokens:
            token_index_dict[token["document_index"]] = token

        schema_scope_constraint_dict = dict()
        for schema_scope_constraint in schema_scope_constraints:
            schema_scope_constraint_dict[
                (
                    schema_scope_constraint["parent_type"]["type"],
                    schema_scope_constraint["child_type"]["type"],
                )
            ] = True

        if count_violations:
            violation_counter._count_scope_tree_violations(
                scope_recommendations,
                schema_scope_constraint_dict,
                token_index_dict,
            )

        scope_recommendations = self.__add_root(
            scope_recommendations, token_index_dict, schema_scope_dict
        )

        scope_recommendations = self.__fix_tree_position(scope_recommendations)

        scope_recommendations, _ = self.extend_child_scopes(
            scope_recommendations, token_index_dict
        )

        change = True
        while change:
            scope_recommendations, incorrect_scope_change = (
                self.__move_up_incorrect_scopes(
                    scope_recommendations, schema_scope_constraint_dict
                )
            )

            scope_recommendations, merge_consecutive_scope_change = (
                self.__merge_consecutive_scopes(
                    scope_recommendations,
                )
            )
            scope_recommendations, missing_children_scope_change = (
                self.__replace_scopes_with_missing_children(scope_recommendations)
            )

            scope_recommendations, move_up_scope_change = self.__move_up_bottom_scopes(
                scope_recommendations, token_index_dict
            )
            change = (
                incorrect_scope_change
                or merge_consecutive_scope_change
                or missing_children_scope_change
                or move_up_scope_change
            )

        scope_recommendations = self.__merge_equal_scopes(scope_recommendations)
        scope_recommendations = sorted(
            scope_recommendations,
            key=lambda x: (
                x["token_start"]["id"],
                -x["token_end"]["id"],
                x["id"],
            ),
        )
        violation_counter.total_scopes_postprocessed = len(scope_recommendations)
        if count_violations:
            violation_counter._log_concept_violations()

        return scope_recommendations

    def __add_root(self, scope_recommendations, token_index_dict, schema_scope_dict):
        max_token = token_index_dict[max(token_index_dict.keys())]
        root = None
        for scope in scope_recommendations:
            if scope["token_end"]["document_index"] > max_token["document_index"]:
                scope["token_end"] = max_token
            if scope["schema_scope"]["type"] == "root":
                scope["parent_scope_id"] = None
                root = scope
        if root:
            return scope_recommendations
        root = {
            "parent_scope_id": None,
            "token_start": token_index_dict[0],
            "token_end": max_token,
            "id": 1000 + len(scope_recommendations),
            "schema_scope": schema_scope_dict["root"],
        }
        for scope in scope_recommendations:
            if scope.get("parent_scope_id") is None or scope["parent_scope_id"] == -1:
                scope["parent_scope_id"] = root["id"]
        scope_recommendations.append(root)
        return scope_recommendations

    def __fix_tree_position(self, scope_recommendations):
        # Rule: Reorder tree, so that possible parent with the closest token range is chosen as parent
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation
        for scope in scope_recommendations:
            best_parent = _find_best_parent(scope, recommendation_id_dict)
            if best_parent and scope.get("parent_scope_id") != best_parent["id"]:
                scope["parent_scope_id"] = best_parent["id"]

        return scope_recommendations

    def extend_child_scopes(self, scope_recommendations, token_index_dict):
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
                key=lambda x: x["token_start"]["document_index"],
            )
            parent = recommendation_id_dict[key]
            first_child = parent_children_dict[key][0]
            last_child = parent_children_dict[key][-1]
            if (
                recommendation_id_dict[first_child["id"]]["token_start"][
                    "document_index"
                ]
                != parent["token_start"]["document_index"]
            ) or (
                recommendation_id_dict[last_child["id"]]["token_end"]["document_index"]
                != parent["token_end"]["document_index"]
            ):
                scope_violations += 1
                recommendation_id_dict[first_child["id"]]["token_start"] = parent[
                    "token_start"
                ]
                recommendation_id_dict[last_child["id"]]["token_end"] = parent[
                    "token_end"
                ]

            for i, child in enumerate(parent_children_dict[key][1:]):
                if (
                    recommendation_id_dict[child["id"]]["token_start"]["document_index"]
                    != parent_children_dict[key][i]["token_end"]["document_index"] + 1
                ):
                    if (
                        parent_children_dict[key][i]["token_end"]
                        == token_index_dict[max(token_index_dict.keys())]
                    ):
                        recommendation_id_dict[child["id"]]["token_start"] = (
                            token_index_dict[max(token_index_dict.keys())]
                        )
                    else:
                        recommendation_id_dict[child["id"]]["token_start"] = (
                            token_index_dict[
                                (
                                    parent_children_dict[key][i]["token_end"][
                                        "document_index"
                                    ]
                                    + 1
                                )
                            ]
                        )
                    scope_violations += 1
        return recommendation_id_dict.values(), scope_violations

    def __merge_consecutive_scopes(
        self,
        scope_recommendations,
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

        at_least_one_change = False
        for key in parent_children_dict:
            if len(parent_children_dict[key]) == 0:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["token_start"]["document_index"],
            )
            merged = parent_children_dict[key][0]
            merged_scope_id_mapping[merged["id"]] = merged["id"]

            if len(parent_children_dict[key]) == 1:
                merged_scopes.append(merged)
            else:
                for scope in parent_children_dict[key][1:]:
                    if (
                        scope["schema_scope"]["horizontal_merging"]
                        and scope["schema_scope"]["type"]
                        == merged["schema_scope"]["type"]
                        and scope["token_start"]["document_index"]
                        == merged["token_end"]["document_index"] + 1
                    ):
                        at_least_one_change = True
                        merged_scope_id_mapping[scope["id"]] = merged["id"]
                        for s in parent_children_dict[scope["id"]]:
                            parent_children_dict[merged["id"]].append(s)
                        parent_children_dict[scope["id"]] = []
                        merged = {
                            "id": merged["id"],
                            "schema_scope": merged["schema_scope"],
                            "token_start": merged["token_start"],
                            "token_end": scope["token_end"],
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
        return merged_scopes, at_least_one_change

    def __move_up_incorrect_scopes(
        self, scope_recommendations, schema_scope_constraint_dict
    ):
        # Rule: replace parent with children if parent-child-relation is not allowed or vertical scope merging is allowed
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        at_least_one_change = False
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
                    if not schema_scope_constraint_dict.get(
                        (
                            parent["schema_scope"]["type"],
                            child["schema_scope"]["type"],
                        )
                    ) or (
                        parent["schema_scope"]["vertical_merging"]
                        and parent["schema_scope"]["type"]
                        == child["schema_scope"]["type"]
                    ):
                        change = True
                        at_least_one_change = True
                        for child_child in parent_children_dict[child["id"]]:
                            recommendation_id_dict[child_child["id"]][
                                "parent_scope_id"
                            ] = child["parent_scope_id"]
                        if parent_children_dict[child["id"]]:
                            parent_children_dict[child["id"]] = []
                        if recommendation_id_dict.get(child["id"]):
                            del recommendation_id_dict[child["id"]]
                if change:
                    break

        return recommendation_id_dict.values(), at_least_one_change

    def __move_up_bottom_scopes(self, scope_recommendations, token_index_dict):
        # Rule: process-irrelevant scopes can be moved up to higher tree-level, if they are the first/last scope inside a parent
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        at_least_one_change = False
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
                    or recommendation_id_dict[key]["schema_scope"]["type"] == "root"
                ):
                    continue
                parent_children_dict[key] = sorted(
                    parent_children_dict[key],
                    key=lambda x: x["token_start"]["document_index"],
                )
                first_child = parent_children_dict[key][0]
                parent = recommendation_id_dict[key]
                if (
                    not first_child["schema_scope"]["process_relevant"]
                    and first_child["token_start"]["document_index"]
                    == recommendation_id_dict[key]["token_start"]["document_index"]
                ):
                    change = True
                    at_least_one_change = True
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
                        parent["token_start"] = token_index_dict[
                            (first_child["token_end"]["document_index"] + 1)
                        ]

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
                    or recommendation_id_dict[key]["schema_scope"]["type"] == "root"
                ):
                    continue
                parent_children_dict[key] = sorted(
                    parent_children_dict[key],
                    key=lambda x: x["token_start"]["document_index"],
                )
                last_child = parent_children_dict[key][-1]
                parent = recommendation_id_dict[key]
                if (
                    not last_child["schema_scope"]["process_relevant"]
                    and last_child["token_end"]["document_index"]
                    == recommendation_id_dict[key]["token_end"]["document_index"]
                ):
                    change = True
                    at_least_one_change = True
                    last_child["parent_scope_id"] = parent["parent_scope_id"]
                    parent["token_end"] = token_index_dict[
                        (last_child["token_start"]["document_index"] - 1)
                    ]
        return recommendation_id_dict.values(), at_least_one_change

    def __replace_scopes_with_missing_children(self, scope_recommendations):
        # Rule: if a scope has invalid number of children, delete it and replace with the children
        recommendation_id_dict = dict()
        for scope_recommendation in scope_recommendations:
            recommendation_id_dict[scope_recommendation["id"]] = scope_recommendation

        at_least_one_change = False
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
                    if child["schema_scope"]["process_relevant"]:
                        count_procedural_children += 1

                parent = recommendation_id_dict[key]
                if parent["schema_scope"][
                    "minimum_children_process_relevant"
                ] > count_procedural_children or (
                    parent["schema_scope"]["maximum_children_process_relevant"]
                    is not None
                    and count_procedural_children
                    > parent["schema_scope"]["maximum_children_process_relevant"]
                ):
                    change = True
                    at_least_one_change = True
                    for child in parent_children_dict[key]:
                        recommendation_id_dict[child["id"]]["parent_scope_id"] = parent[
                            "parent_scope_id"
                        ]
                    del recommendation_id_dict[key]
                    parent_children_dict[key] = []
        return recommendation_id_dict.values(), at_least_one_change

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
            if (
                scope_id_dict[key]["schema_scope"]["type"]
                != scope["schema_scope"]["type"]
            ):
                continue

            if (
                scope_id_dict[key]["token_start"]["document_index"]
                == scope["token_start"]["document_index"]
                and scope_id_dict[key]["token_end"]["document_index"]
                == scope["token_end"]["document_index"]
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
        logger.info(log_message)

    def _count_scope_tree_violations(
        self,
        scope_recommendations,
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
            if scope["schema_scope"]["type"] == "root":
                self.root_missing = False
                break

        # Check if max token is exceeded
        for scope in scope_recommendations:
            if scope["token_end"]["document_index"] >= len(token_index_dict):
                self.max_token_exceeded += 1

        # Count how often scope is at wrong position in tree
        for scope in scope_recommendations:
            best_parent = _find_best_parent(scope, recommendation_id_dict)
            if best_parent and scope.get("parent_scope_id") != best_parent["id"]:
                self.wrong_tree_position += 1

        # Count gaps in between, at the beginning and at the end of a subtree
        for key in parent_children_dict:
            if len(parent_children_dict[key]) == 0 or key is None:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["token_start"]["document_index"],
            )
            parent = recommendation_id_dict[key]
            first_child = parent_children_dict[key][0]
            last_child = parent_children_dict[key][-1]
            if (
                recommendation_id_dict[first_child["id"]]["token_start"][
                    "document_index"
                ]
                < parent["token_start"]["document_index"]
            ) or (
                recommendation_id_dict[last_child["id"]]["token_end"]["document_index"]
                > parent["token_end"]["document_index"]
            ):
                self.child_exceeding_parent += 1

            if (
                recommendation_id_dict[first_child["id"]]["token_start"][
                    "document_index"
                ]
                > parent["token_start"]["document_index"]
            ):
                self.first_child_later_start += 1
            if (
                recommendation_id_dict[last_child["id"]]["token_end"]["document_index"]
                < parent["token_end"]["document_index"]
            ):
                self.last_child_earlier_end += 1
            for i, child in enumerate(parent_children_dict[key][1:]):
                if (
                    recommendation_id_dict[child["id"]]["token_start"]["document_index"]
                    != parent_children_dict[key][i]["token_end"]["document_index"] + 1
                ):
                    if (
                        recommendation_id_dict[child["id"]]["token_start"][
                            "document_index"
                        ]
                        > parent_children_dict[key][i]["token_end"]["document_index"]
                        + 1
                    ):
                        self.gaps_in_between += 1
                    else:
                        self.scope_overlapping += 1

        for key in parent_children_dict:
            if len(parent_children_dict[key]) <= 1:
                continue
            parent_children_dict[key] = sorted(
                parent_children_dict[key],
                key=lambda x: x["token_start"]["document_index"],
            )

            for i, scope in enumerate(parent_children_dict[key][1:]):
                if (
                    scope["schema_scope"]["horizontal_merging"]
                    and scope["schema_scope"]["type"]
                    == parent_children_dict[key][i]["schema_scope"]["type"]
                    and scope["token_start"]["document_index"]
                    == parent_children_dict[key][i]["token_end"]["document_index"] + 1
                ):
                    self.horizontal_unmerged += 1

        for key in list(parent_children_dict.keys()):
            if len(parent_children_dict[key]) == 0 or key is None:
                continue

            parent = recommendation_id_dict[key]
            for child in parent_children_dict[key]:

                if (
                    parent["schema_scope"]["vertical_merging"]
                    and parent["schema_scope"]["type"] == child["schema_scope"]["type"]
                ):
                    self.vertical_unmerged += 1
                elif not schema_scope_constraint_dict.get(
                    (parent["schema_scope"]["type"], child["schema_scope"]["type"])
                ):
                    if (
                        parent["schema_scope"]["type"] == "root"
                        and child["schema_scope"]["type"] == "sequential"
                    ):
                        self.vertical_unmerged += 1
                    else:
                        self.parent_child_forbidden += 1
        for key in parent_children_dict.keys():
            if len(parent_children_dict[key]) == 0 or key is None:
                continue
            count_procedural_children = 0
            for child in parent_children_dict[key]:
                if child["schema_scope"]["process_relevant"]:
                    count_procedural_children += 1
            parent = recommendation_id_dict[key]
            if (
                parent["schema_scope"]["minimum_children_process_relevant"]
                > count_procedural_children
            ):
                self.too_few_children += 1
            elif (
                parent["schema_scope"]["maximum_children_process_relevant"] is not None
                and count_procedural_children
                > parent["schema_scope"]["maximum_children_process_relevant"]
            ):
                self.too_many_children += 1

        return recommendation_id_dict.values()


def _find_best_parent(scope, recommendation_id_dict):
    best_parent = recommendation_id_dict.get(scope["parent_scope_id"])
    if scope["schema_scope"]["type"] == "root":
        return None
    parent = best_parent
    for scope_rec in recommendation_id_dict.values():
        if scope["parent_scope_id"] == scope_rec["id"]:
            parent = scope_rec

    if (
        best_parent["token_start"]["document_index"]
        > scope["token_end"]["document_index"]
        or best_parent["token_end"]["document_index"]
        < scope["token_start"]["document_index"]
    ):
        best_parent = None
    elif parent is not None and (
        parent["token_start"]["document_index"] > scope["token_start"]["document_index"]
        or parent["token_end"]["document_index"] < scope["token_end"]["document_index"]
    ):
        # Child exceeding parent => other violation
        return best_parent
    for possible_parent in recommendation_id_dict.values():
        if (
            possible_parent["token_start"] == scope["token_start"]
            and possible_parent["token_end"] == scope["token_end"]
        ):
            continue
        if (
            possible_parent["id"] == scope["id"]
            or possible_parent["schema_scope"].get("maximum_children_process_relevant")
            == 0
        ):
            continue

        if (
            possible_parent["token_start"]["document_index"]
            <= scope["token_start"]["document_index"]
            and possible_parent["token_end"]["document_index"]
            >= scope["token_end"]["document_index"]
        ):

            if not best_parent or (
                (
                    possible_parent["token_end"]["document_index"]
                    - possible_parent["token_start"]["document_index"]
                )
                <= (
                    best_parent["token_end"]["document_index"]
                    - best_parent["token_start"]["document_index"]
                )
            ):
                if best_parent and (
                    possible_parent["token_start"] == best_parent["token_start"]
                    and possible_parent["token_end"] == best_parent["token_end"]
                ):
                    if (
                        possible_parent["id"] > best_parent["id"]
                        and not possible_parent["id"] == best_parent["parent_scope_id"]
                    ):  # only works if higher branching scopes have lower ids
                        best_parent = possible_parent
                else:
                    best_parent = possible_parent
    return best_parent


scope_postprocess_service = ScopePostprocessService()
