import copy
import logging
from scipy.optimize import linear_sum_assignment
import numpy as np
from werkzeug.exceptions import BadRequest

from app.models import DocumentEdit
from app.repositories.scope_repository import ScopeRepository
from app.services.document_recommendation_service import (
    document_recommendation_service,
    DocumentRecommendationService,
)
from app.services.schema_scope_service import SchemaScopeService, schema_scope_service
from app.services.schema_service import SchemaService, schema_service
from app.services.scope_postprocess_service import (
    ScopePostprocessService,
    scope_postprocess_service,
)
from app.services.token_service import TokenService, token_service
import itertools


class ScopeService:
    __scope_repository: ScopeRepository
    scope_postprocess_service: ScopePostprocessService
    token_service: TokenService
    schema_service: SchemaService
    schema_scope_service: SchemaScopeService
    document_recommendation_service: DocumentRecommendationService

    def __init__(
        self,
        scope_repository,
        scope_postprocess_service,
        token_service,
        schema_service,
        schema_scope_service,
        document_recommendation_service,
    ):
        self.__scope_repository = scope_repository
        self.scope_postprocess_service = scope_postprocess_service
        self.token_service = token_service
        self.schema_service = schema_service
        self.schema_scope_service = schema_scope_service
        self.document_recommendation_service = document_recommendation_service

    def get_scope_tree_by_document_edit_id(self, document_edit_id):
        scope = self.__scope_repository.get_scope_tree_by_document_edit(
            document_edit_id
        )
        if not scope:
            raise BadRequest("Root Node does not exist")
        return scope.to_json()

    def get_scope_list_by_document_edit_id(self, document_edit_id):
        scope_list = self.__scope_repository.get_scopes_by_document_edit(
            document_edit_id
        )
        return [scope.to_flat() for scope in scope_list]

    def create_scope(
        self,
        schema_scope_id,
        token_start_id,
        token_end_id,
        document_edit_id,
        parent_scope_id=None,
    ):
        # Check Tokens in document
        self.token_service.check_tokens_in_document_edit(
            [token_start_id, token_end_id], document_edit_id
        )

        # Check Scope Type is allowed
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_scope = self.schema_scope_service.get_schema_scope_by_id(schema_scope_id)
        if schema_scope.schema_id != schema.id:
            raise BadRequest("Scope Type not allowed")

        scope_tree = self.get_scope_tree_by_document_edit_id(document_edit_id)
        constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )
        if parent_scope_id is not None:
            parent = self.__get_scope_in_tree(scope_tree, parent_scope_id)
            if parent is None:
                raise BadRequest("Parent scope not part of document edit")
        else:
            parent = scope_tree
            parent_scope_id = parent["id"]

        self.__verify_tokens_non_overlapping(parent, token_start_id, token_end_id)

        self.__verify_schema_constraints(
            constraints, schema_scope_id, parent["schema_scope"]["id"]
        )

        return self.__scope_repository.create_scope(
            schema_scope_id,
            token_start_id,
            token_end_id,
            parent_scope_id,
            document_edit_id,
        )

    def __get_scope_in_tree(self, tree, scope_id):
        if tree is None:
            return None
        if tree["id"] == scope_id:
            return tree
        for child in tree["children"]:
            sub_tree = self.__get_scope_in_tree(child, scope_id)
            if sub_tree:
                return sub_tree
        return None

    def __verify_tokens_non_overlapping(self, parent, token_start_id, token_end_id):
        token_start = self.token_service.get_token_by_id(token_start_id).to_json()
        token_end = self.token_service.get_token_by_id(token_end_id).to_json()
        if token_start["document_index"] > token_end["document_index"]:
            raise BadRequest("Start token comes after the end token")
        if (
            parent["token_start"]["document_index"] > token_start["document_index"]
            or parent["token_end"]["document_index"] < token_end["document_index"]
        ):
            raise BadRequest("Tokens of scope exceed parent scope")
        for child in parent["children"]:
            if not (
                token_end["document_index"] < child["token_start"]["document_index"]
                or token_start["document_index"] > child["token_end"]["document_index"]
            ):
                raise BadRequest("Scope overlaps with other scope")

    def __verify_schema_constraints(
        self, constraints, child_schema_scope_id, parent_schema_scope_id
    ):
        for constraint in constraints:
            if (
                constraint["parent_type"]["id"] == parent_schema_scope_id
                and constraint["child_type"]["id"] == child_schema_scope_id
            ):
                return True
        raise BadRequest("No matching constraint found")

    def create_root_scope(self, document_edit_id, document_id, schema_id):
        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        max_token = tokens[0]
        min_token = tokens[0]
        for token in tokens:
            if token["document_index"] > max_token["document_index"]:
                max_token = token
            if token["document_index"] == 0:
                min_token = token
        schema_scope_root_id = (
            self.schema_scope_service.get_schema_scope_root_by_schema_id(schema_id).id
        )
        token_start_id = min_token["id"]
        token_end_id = max_token["id"]
        scope_tree = self.__scope_repository.get_scope_tree_by_document_edit(
            document_edit_id
        )
        if scope_tree:
            raise BadRequest("Root Node already exists")
        self.__scope_repository.create_scope(
            schema_scope_root_id,
            token_start_id,
            token_end_id,
            document_edit_id=document_edit_id,
        )

    def scope_tree_similarity_obj(self, ref, comp, tokens, schema_scopes, method=None):
        reference_leafs = self.__get_tree_leafs_with_parents_rec(ref)
        comparison_leafs = self.__get_tree_leafs_with_parents_rec(comp)
        token_dict = {token["document_index"]: token for token in tokens}
        process_relevant_schema_scope_ids = [
            s["id"] for s in schema_scopes if s["process_relevant"]
        ]

        min_len = min(len(reference_leafs), len(comparison_leafs))
        similarity_matrix = np.zeros((len(reference_leafs), len(comparison_leafs)))
        for i, r in enumerate(reference_leafs):
            for j, c in enumerate(comparison_leafs):
                if method == "only_leafs":
                    similarity_matrix[i, j] = self.__scope_similarity_leafs(r, c)
                elif method == "lcs":
                    similarity_matrix[i, j] = self.__scope_similarity_partial_path(
                        r, c, process_relevant_schema_scope_ids
                    )
                else:
                    similarity_matrix[i, j] = self.__scope_similarity(
                        r, c, process_relevant_schema_scope_ids
                    )

        row_ind, col_ind = linear_sum_assignment(-similarity_matrix)
        # logging.info(row_ind)
        # logging.info(col_ind)
        # Compute final score
        total_sim = similarity_matrix[row_ind, col_ind].sum()
        # logging.info(total_sim / min_len)

        similarity_per_scope = []
        for i, leaf in enumerate(reference_leafs):
            score = 0
            idx = 0
            for row in row_ind:
                if row == i:
                    score = similarity_matrix[row_ind[idx], col_ind[idx]]
                    break
                idx += 1
            similarity_per_scope.append(
                {
                    "token_start": token_dict[leaf["token_start"]],
                    "token_end": token_dict[leaf["token_end"]],
                    "similarity": score,
                }
            )
            # logging.info(
            #    "Similarity for scope {}: {}".format(
            #        (leaf["token_start"], leaf["token_end"]), score
            #    )
            # )

        ref = []
        for leaf in reference_leafs:
            ref.append((leaf["token_start"], leaf["token_end"]))
        comp = []
        for leaf in comparison_leafs:
            comp.append((leaf["token_start"], leaf["token_end"]))
        # logging.info(ref)
        # logging.info(comp)
        # logging.info(similarity_matrix)
        # One-to-Many:
        # total_sim = np.sum(np.max(similarity_matrix, axis=1))
        # logging.info(total_sim)
        # total_sim = np.sum(np.max(similarity_matrix, axis=0))
        # logging.info(total_sim)

        # Partial Path
        # similarity_matrix = np.zeros((len(reference_leafs), len(comparison_leafs)))
        # for i, r in enumerate(reference_leafs):
        #    for j, c in enumerate(comparison_leafs):
        #        similarity_matrix[i, j] = self.__scope_similarity_partial_path(
        #            r.copy(), c.copy(), process_relevant_schema_scope_ids
        #        )
        # row_ind, col_ind = linear_sum_assignment(-similarity_matrix)
        # total_sim = similarity_matrix[row_ind, col_ind].sum()
        # logging.info(total_sim / len(reference_leafs))
        # logging.info(total_sim / len(comparison_leafs))
        # logging.info(total_sim)

        return {
            "total_similarity": total_sim / min_len,
            "#reference_scopes": len(reference_leafs),
            "#comparison_scopes": len(comparison_leafs),
            "similarity_per_scope": similarity_per_scope,
        }

    def scope_tree_similarity_obj_branches(self, ref, comp):
        min_len = min(len(ref), len(comp))
        similarity_matrix = np.zeros((len(ref), len(comp)))
        for i, r in enumerate(ref):
            for j, c in enumerate(comp):
                similarity_matrix[i, j] = self.__scope_similarity_branches(r, c)
        row_ind, col_ind = linear_sum_assignment(-similarity_matrix)
        total_sim = similarity_matrix[row_ind, col_ind].sum()
        logging.info(total_sim / min_len)

        logging.info(total_sim / len(ref))
        logging.info(total_sim / len(comp))
        logging.info(len(ref))

        return {
            "total_similarity": total_sim / min_len,
        }

    def scope_tree_similarity(
        self, reference_document_edit_id, comparison_document_edit_id, method
    ):
        reference_document_edit = self.__scope_repository.get_object_by_id(
            DocumentEdit, reference_document_edit_id
        )

        tokens = self.token_service.get_tokens_by_document(
            reference_document_edit.document_id
        )["tokens"]

        comparison_document_edit = self.__scope_repository.get_object_by_id(
            DocumentEdit, comparison_document_edit_id
        )
        if (
            not reference_document_edit.document_id
            == comparison_document_edit.document_id
        ):
            raise BadRequest("Comparison of different documents not possible")

        schema = self.schema_service.get_schema_by_document_edit(
            reference_document_edit_id
        )

        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )

        reference_tree_scopes = self.get_scope_tree_by_document_edit_id(
            reference_document_edit_id
        )
        comparison_tree_scopes = self.get_scope_tree_by_document_edit_id(
            comparison_document_edit_id
        )
        return self.scope_tree_similarity_obj(
            reference_tree_scopes, comparison_tree_scopes, tokens, schema_scopes, method
        )

    def scope_tree_similarity_list(
        self,
        reference_document_edit_id_list,
        comparison_document_edit_id_list,
        method=None,
    ):
        first_document_edit_id = self.__scope_repository.get_object_by_id(
            DocumentEdit, reference_document_edit_id_list[0]
        )

        tokens = self.token_service.get_tokens_by_document(
            first_document_edit_id.document_id
        )["tokens"]

        schema = self.schema_service.get_schema_by_document_edit(
            first_document_edit_id.id
        )

        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )

        reference_tree_scopes_list = [
            self.get_scope_tree_by_document_edit_id(
                reference_document_edit_id
            )  # self.get_scope_list_by_document_edit_id
            for reference_document_edit_id in reference_document_edit_id_list
        ]
        comparison_tree_scopes_list = [
            self.get_scope_tree_by_document_edit_id(
                comparison_document_edit_id
            )  # self.get_scope_list_by_document_edit_id
            for comparison_document_edit_id in comparison_document_edit_id_list
        ]

        similarity_matrix = np.zeros(
            (
                len(reference_document_edit_id_list),
                len(comparison_document_edit_id_list),
            )
        )
        for i, r in enumerate(reference_tree_scopes_list):
            for j, c in enumerate(comparison_tree_scopes_list):
                similarity_matrix[i, j] = self.scope_tree_similarity_obj(
                    r, c, tokens, schema_scopes, method
                )[  # self.scope_tree_similarity_obj_branches(r, c)
                    "total_similarity"
                ]

        max_per_row = np.max(
            similarity_matrix, axis=1
        )  # max similarity of human to any llm annotation
        max_per_column = np.max(
            similarity_matrix, axis=0
        )  # max similarity of llm to any human annotation

        logging.info(
            f"Diversity: {[round(float(mpr), 4) for mpr in max_per_row]}, Average: {round(np.mean(max_per_row),4)}, Standard Deviation: {round(np.std(max_per_row), 4)}"
        )
        logging.info(
            f"Quality: {[round(float(mpc), 4) for mpc in max_per_column]}, Average: {round(np.mean(max_per_column),4)}, Standard Deviation: {round(np.std(max_per_column), 4)}"
        )
        logging.info(
            f"Overall similarity: {round(np.mean([np.mean(max_per_row), np.mean(max_per_column)]), 4)}"
        )

        return None

    def scope_tree_similarity_list_self(
        self,
        reference_document_edit_id_list,
    ):
        first_document_edit_id = self.__scope_repository.get_object_by_id(
            DocumentEdit, reference_document_edit_id_list[0]
        )

        tokens = self.token_service.get_tokens_by_document(
            first_document_edit_id.document_id
        )["tokens"]

        schema = self.schema_service.get_schema_by_document_edit(
            first_document_edit_id.id
        )

        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )

        reference_tree_scopes_list = [
            self.get_scope_tree_by_document_edit_id(
                reference_document_edit_id
            )  # self.get_scope_list_by_document_edit_id
            for reference_document_edit_id in reference_document_edit_id_list
        ]

        similarity_matrix = []
        similarity_matrix_lcs = []
        for i, r in enumerate(reference_tree_scopes_list):
            for j, c in enumerate(reference_tree_scopes_list):
                if i < j:

                    similarity_matrix.append(
                        self.scope_tree_similarity_obj(
                            r, c, tokens, schema_scopes
                        )[  # self.scope_tree_similarity_obj_branches(r, c)
                            "total_similarity"
                        ]
                    )
                    similarity_matrix_lcs.append(
                        self.scope_tree_similarity_obj(
                            r, c, tokens, schema_scopes, method="lcs"
                        )[  # self.scope_tree_similarity_obj_branches(r, c)
                            "total_similarity"
                        ]
                    )

        # logging.info(
        #    f"conservative: {[round(float(s),4) for s in similarity_matrix]}, Average: {round(np.mean(similarity_matrix), 4)}, Standard Deviation: {round(np.std(similarity_matrix), 4)}"
        # )
        logging.info(
            f"lcs: {[round(float(s),4) for s in similarity_matrix_lcs]}, Average: {round(np.mean(similarity_matrix_lcs),4)}, Standard Deviation: {round(np.std(similarity_matrix_lcs), 4)}"
        )

        return None

    def __scope_similarity_branches(self, reference_scope, comparison_scope):
        if reference_scope["scope_type"] != comparison_scope["scope_type"]:
            return 0
        reference_tokens = set(
            range(
                reference_scope["startTokenDocumentIndex"],
                reference_scope["endTokenDocumentIndex"] + 1,
            )
        )
        comparison_tokens = set(
            range(
                comparison_scope["startTokenDocumentIndex"],
                comparison_scope["endTokenDocumentIndex"] + 1,
            )
        )

        intersection = reference_tokens & comparison_tokens
        union = reference_tokens | comparison_tokens

        if not union:
            return 0.0
        return len(intersection) / len(union)

    def __scope_similarity(
        self, reference_scope, comparison_scope, process_relevant_schema_scope_ids
    ):
        if reference_scope["path"] != comparison_scope["path"]:
            if (  # irrelevant/related: Layer does not matter
                reference_scope["path"][-1] not in process_relevant_schema_scope_ids
                and reference_scope["path"][-1] == comparison_scope["path"][-1]
            ):
                return self.__jaccard_token_overlap(reference_scope, comparison_scope)
            else:
                return 0

        score = 1
        ref_children_path = reference_scope["children_num_path"][1:-1]
        comp_children_path = comparison_scope["children_num_path"][1:-1]
        ref_token_path = reference_scope["token_path"][1:]
        comp_token_path = comparison_scope["token_path"][1:]
        if len(reference_scope["path"][1:-1]):
            for i in range(len(reference_scope["path"][1:-1])):
                score *= self.__jaccard_token_overlap(
                    ref_token_path[i], comp_token_path[i]
                )
                # (
                # float(ref_children_path[i]) / comp_children_path[i]
                # if ref_children_path[i] < comp_children_path[i]
                # else float(comp_children_path[i]) / ref_children_path[i]
                # )

        return self.__jaccard_token_overlap(reference_scope, comparison_scope, score)

    def __scope_similarity_leafs(self, reference_scope, comparison_scope):
        if reference_scope["path"][-1] != comparison_scope["path"][-1]:
            return 0
        return self.__jaccard_token_overlap(reference_scope, comparison_scope)

    def __scope_similarity_partial_path(
        self, reference_scope, comparison_scope, process_relevant_schema_scope_ids
    ):
        ref_path = reference_scope["path"][1:]
        comp_path = comparison_scope["path"][1:]
        ref_children_path = reference_scope["children_num_path"][1:]
        comp_children_path = comparison_scope["children_num_path"][1:]
        ref_token_path = reference_scope["token_path"][1:]
        comp_token_path = comparison_scope["token_path"][1:]

        def __sequence_matching(ref, comp):

            max_len = max(len(ref), len(comp))
            if max_len == 0:
                return 1
            m, n = len(ref), len(comp)
            matrix = np.zeros((m + 1, n + 1))
            for i in range(m):
                for j in range(n):
                    if ref[i] == comp[j]:
                        score = self.__jaccard_token_overlap(
                            ref_token_path[i], comp_token_path[j]
                        )
                        # (
                        # float(ref_children_path[i]) / comp_children_path[j]
                        # if ref_children_path[i] < comp_children_path[j]
                        # else float(comp_children_path[j]) / ref_children_path[i]
                        # )
                    else:
                        score = 0.0

                    if matrix[i + 1][j + 1] < matrix[i][j] + score:
                        matrix[i + 1][j + 1] = matrix[i][j] + score

                    if matrix[i + 1][j] < matrix[i][j]:
                        matrix[i + 1][j] = matrix[i][j]

                    if matrix[i][j + 1] < matrix[i][j]:
                        matrix[i][j + 1] = matrix[i][j]
            return np.max(matrix) / float(max_len)

        token_overlap = self.__jaccard_token_overlap(
            reference_scope, comparison_scope, 1
        )
        if token_overlap == 0:
            return 0
        if reference_scope["path"][-1] != comparison_scope["path"][-1]:
            similarity = 0
        elif (
            reference_scope["path"][-1] == comparison_scope["path"][-1]
            and reference_scope["path"][-1] not in process_relevant_schema_scope_ids
        ):
            similarity = 1
        else:
            similarity = __sequence_matching(ref_path[:-1], comp_path[:-1])

        return similarity * token_overlap

    def __jaccard_token_overlap(self, reference_scope, comparison_scope, similarity=1):
        reference_tokens = set(
            range(reference_scope["token_start"], reference_scope["token_end"] + 1)
        )
        comparison_tokens = set(
            range(comparison_scope["token_start"], comparison_scope["token_end"] + 1)
        )

        intersection = reference_tokens & comparison_tokens
        union = reference_tokens | comparison_tokens

        if not union:
            return 0.0
        return len(intersection) / len(union) * similarity

    def __get_tree_leafs_with_parents_rec(
        self, scope_tree, path=None, children_num_path=None, token_path=None
    ):
        path = (path or []) + [scope_tree["schema_scope"]["id"]]
        children_num = 0
        for child in scope_tree["children"]:
            if child["schema_scope"]["process_relevant"]:
                children_num += 1

        children_num_path = (children_num_path or []) + [children_num]
        token_path = (token_path or []) + [
            {
                "token_start": scope_tree["token_start"]["document_index"],
                "token_end": scope_tree["token_end"]["document_index"],
            }
        ]
        leaf_scopes = []
        if not scope_tree["children"]:
            return [
                {
                    "path": path,
                    "token_start": scope_tree["token_start"]["document_index"],
                    "token_end": scope_tree["token_end"]["document_index"],
                    "children_num_path": children_num_path,
                    "token_path": token_path,
                }
            ]
        for child in scope_tree["children"]:
            leaf_scopes.extend(
                self.__get_tree_leafs_with_parents_rec(
                    child, path, children_num_path, token_path
                )
            )
        return leaf_scopes

    def __get_schema_scopes_without_children(self, schema_scope_constraints):
        schema_scopes = {s["child_type"]["id"]: True for s in schema_scope_constraints}
        for constraint in schema_scope_constraints:
            if constraint["parent_type"]["id"] in schema_scopes:
                del schema_scopes[constraint["parent_type"]["id"]]
        return schema_scopes.keys()

    def get_scope_interpretations(
        self, document_id, document_content, model, num_interpretations, req_params
    ):
        schema = self.schema_service.get_schema_by_document(document_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )

        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        interpretation_list = []
        raw_list = []
        req_params = dict(req_params)
        req_params["cache_datetime"] = 1
        if req_params.get("bottom_up"):
            del req_params["bottom_up"]
            req_params["only_leafs"] = 1
            leafs_list = []
            for _ in range(num_interpretations):
                leafs = self.document_recommendation_service.get_scope_recommendation(
                    schema_scopes,
                    schema_scope_constraints,
                    document_content,
                    tokens,
                    document_id,
                    model,
                    req_params,
                    leafs_list if req_params.get("pass_interpretations") else None,
                    map_to_scopes=False,
                )
                for _ in range(0, 2 if req_params.get("pass_interpretations") else 1):
                    scope_recommendation = self.document_recommendation_service.get_scope_recommendation_branches(
                        schema_scopes,
                        schema_scope_constraints,
                        document_content,
                        tokens,
                        leafs,
                        document_id,
                        model,
                        req_params,
                        raw_list if req_params.get("pass_interpretations") else None,
                    )
                    raw_list.append(scope_recommendation)
                    postprocessed_recommendations = (
                        self.scope_postprocess_service.postprocess_scope_tree(
                            scope_recommendation,
                            tokens,
                            schema_scopes,
                            schema_scope_constraints,
                        )
                    )
                    interpretation_list.append(postprocessed_recommendations)

                leafs_list.append(leafs)

        else:
            for _ in range(num_interpretations):
                recommendations = (
                    self.document_recommendation_service.get_scope_recommendation(
                        schema_scopes,
                        schema_scope_constraints,
                        document_content,
                        tokens,
                        document_id,
                        model,
                        req_params,
                        raw_list if req_params.get("pass_interpretations") else None,
                    )
                )

                postprocessed_recommendations = (
                    self.scope_postprocess_service.postprocess_scope_tree(
                        recommendations,
                        tokens,
                        schema_scopes,
                        schema_scope_constraints,
                    )
                )
                raw_list.append(recommendations)
                interpretation_list.append(postprocessed_recommendations)
        self.scope_postprocess_service.counter.log_concept_violations()
        return interpretation_list

    def get_scope_interpretations_branches(
        self,
        document_id,
        document_content,
        model,
        num_interpretations,
        req_params,
        leafs,
    ):
        schema = self.schema_service.get_schema_by_document(document_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )

        tokens = self.token_service.get_tokens_by_document(document_id)["tokens"]
        interpretation_list = []
        raw_list = []
        req_params = dict(req_params)
        req_params["cache_datetime"] = 1

        if req_params.get("only_text"):
            for leaf in leafs:
                leaf["text"] = "".join(
                    token["text"]
                    for token in tokens[
                        leaf["startTokenDocumentIndex"] : leaf["endTokenDocumentIndex"]
                        + 1
                    ]
                )
                del leaf["startTokenDocumentIndex"]
                del leaf["endTokenDocumentIndex"]

        for _ in range(num_interpretations):
            recommendations = (
                self.document_recommendation_service.get_scope_recommendation_branches(
                    schema_scopes,
                    schema_scope_constraints,
                    document_content,
                    tokens,
                    leafs,
                    document_id,
                    model,
                    req_params,
                    raw_list if req_params.get("pass_interpretations") else None,
                )
            )

            postprocessed_recommendations = (
                self.scope_postprocess_service.postprocess_scope_tree(
                    recommendations,
                    tokens,
                    schema_scopes,
                    schema_scope_constraints,
                )
            )
            raw_list.append(recommendations)
            interpretation_list.append(postprocessed_recommendations)
        self.scope_postprocess_service.counter.log_concept_violations()
        return interpretation_list

    def save_scope_recommendations(
        self, document_edit_id, postprocessed_recommendations
    ):
        scopes = []
        scope_id_mapping = {}
        root = self.get_scope_tree_by_document_edit_id(document_edit_id)
        scope_id_mapping[None] = root["id"]
        postprocessed_recommendations = self.tree_to_flat(
            self.rec_to_tree(postprocessed_recommendations)
        )
        for recommendation in postprocessed_recommendations:
            try:
                if recommendation["schema_scope"]["id"] == root["schema_scope"]["id"]:
                    scope_id_mapping[recommendation["id"]] = root["id"]
                else:
                    new_scope = self.create_scope(
                        recommendation["schema_scope"]["id"],
                        recommendation["token_start"]["id"],
                        recommendation["token_end"]["id"],
                        document_edit_id,
                        scope_id_mapping[recommendation.get("parent_scope_id")],
                    )
                    scopes.append(new_scope)
                    scope_id_mapping[recommendation["id"]] = new_scope.id
            except Exception as e:
                logging.info(
                    "Failed to create scope: " + str(recommendation) + ", " + str(e)
                )
        logging.info(f"Recommendations created.")
        return self.get_scope_tree_by_document_edit_id(document_edit_id)

    def get_scope_recommendations(self, document_edit_id, model, params, leafs):
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )

        document_edit = self.__scope_repository.get_object_by_id(
            DocumentEdit, document_edit_id
        )
        tokens = self.token_service.get_tokens_by_document(document_edit.document.id)[
            "tokens"
        ]

        if leafs:
            recommendations = (
                self.document_recommendation_service.get_scope_recommendation_branches(
                    schema_scopes,
                    schema_scope_constraints,
                    document_edit.document.content,
                    tokens,
                    leafs,
                    document_edit.document.id,
                    model,
                    req_params=params,
                )
            )
        else:
            recommendations = (
                self.document_recommendation_service.get_scope_recommendation(
                    schema_scopes,
                    schema_scope_constraints,
                    document_edit.document.content,
                    tokens,
                    document_edit.document.id,
                    model,
                    req_params=params,
                )
            )
        recommendations = self.scope_postprocess_service.postprocess_scope_tree(
            recommendations,
            tokens,
            schema_scopes,
            schema_scope_constraints,
        )
        return self.save_scope_recommendations(document_edit.id, recommendations)

    def get_scope_recommendations_branches(self, document_edit_id, model, params):
        schema = self.schema_service.get_schema_by_document_edit(document_edit_id)
        schema_scopes = self.schema_scope_service.get_schema_scopes_by_schema_id(
            schema.id
        )
        schema_scope_constraints = (
            self.schema_scope_service.get_schema_scope_constraints_by_schema_id(
                schema.id
            )
        )

        document_edit = self.__scope_repository.get_object_by_id(
            DocumentEdit, document_edit_id
        )
        scopes = self.get_scope_list_by_document_edit_id(document_edit_id)
        scopes = [scope for scope in scopes if scope["scope_type"] != "root"]
        tokens = self.token_service.get_tokens_by_document(document_edit.document.id)[
            "tokens"
        ]

        recommendations = (
            self.document_recommendation_service.get_scope_recommendation_branches(
                schema_scopes,
                schema_scope_constraints,
                document_edit.document.content,
                tokens,
                scopes,
                document_edit.document.id,
                model,
                req_params=params,
            )
        )

        recommendations = self.scope_postprocess_service.postprocess_scope_tree(
            recommendations,
            tokens,
            schema_scopes,
            schema_scope_constraints,
        )
        self.delete_scope_tree(document_edit_id)
        return self.save_scope_recommendations(document_edit.id, recommendations)

    def __get_ambiguous_subtrees(self, ref_doc_edit, comp_doc_edit):
        ambiguous_subtrees = []

        def __traverse_subtrees(ref_tree, comp_tree_candidates):
            matched_sub_tree = None
            for comp_tree in comp_tree_candidates:
                if self.__subtrees_equal(ref_tree, comp_tree):
                    matched_sub_tree = comp_tree
                    break
            if not matched_sub_tree:
                next_comps = []
                for comp_tree in comp_tree_candidates:
                    if self.__layer_equal(ref_tree, comp_tree):
                        next_comps.append(comp_tree)
                if not next_comps:
                    ref_tree["parent_scope_id"] = comp_tree_candidates[0][
                        "parent_scope_id"
                    ]
                    ambiguous_subtrees.append(ref_tree)
                else:
                    candidates = []
                    for next_comp in next_comps:
                        for child in next_comp["children"]:
                            candidates.append(child)
                    for ref_child in ref_tree["children"]:
                        __traverse_subtrees(ref_child, candidates)

        __traverse_subtrees(ref_doc_edit, [comp_doc_edit])
        return ambiguous_subtrees

    def __subtrees_equal(self, ref_child, comp_child):
        if (
            ref_child["schema_scope"] != comp_child["schema_scope"]
            or len(ref_child["children"]) != len(comp_child["children"])
            or ref_child["token_start"]["id"] != comp_child["token_start"]["id"]
            or ref_child["token_end"]["id"] != comp_child["token_end"]["id"]
        ):
            return False
        return all(
            self.__subtrees_equal(r, c)
            for r, c in zip(
                sorted(ref_child["children"], key=lambda x: x["token_start"]["id"]),
                sorted(comp_child["children"], key=lambda x: x["token_start"]["id"]),
            )
        )

    def __layer_equal(self, ref_child, comp_child):
        if (
            ref_child["schema_scope"]["type"] != comp_child["schema_scope"]["type"]
            or ref_child["token_start"]["id"] != comp_child["token_start"]["id"]
            or ref_child["token_end"]["id"] != comp_child["token_end"]["id"]
        ):
            return False
        return True

    def get_scope_combinations(self, ref_doc_edit, comp_doc_edit, tokens):
        token_index_dict = {t["document_index"]: t for t in tokens}

        ambiguous_scopes = self.__get_ambiguous_subtrees(ref_doc_edit, comp_doc_edit)

        all_combinations = []
        for r in range(1, len(ambiguous_scopes)):
            all_combinations.extend(itertools.combinations(ambiguous_scopes, r))
        all_combinations = [list(comb) for comb in all_combinations]
        logging.info(len(all_combinations))
        combo_trees = []

        for combination in all_combinations:
            compare_tree = copy.deepcopy(comp_doc_edit)
            for scope in combination:
                parent = self.__get_scope_in_tree(
                    compare_tree, scope["parent_scope_id"]
                )
                new_children = []
                for child in parent["children"]:
                    # case 1: child is completely inside scope => remove child
                    if (
                        child["token_start"]["document_index"]
                        >= scope["token_start"]["document_index"]
                        and child["token_end"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        continue

                    # case 2: child starts inside scope => adjust start
                    elif (
                        scope["token_start"]["document_index"]
                        <= child["token_start"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        continue

                    # case 3: scope is completely inside child => remove child
                    elif (
                        child["token_start"]["document_index"]
                        <= scope["token_start"]["document_index"]
                        and child["token_end"]["document_index"]
                        >= scope["token_end"]["document_index"]
                    ):
                        continue

                    # case 4: child ends inside scope => adjust end
                    elif (
                        scope["token_start"]["document_index"]
                        <= child["token_end"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        continue
                    else:
                        new_children.append(child)

                    parent["children"] = new_children
                parent["children"].append(scope)
            compare_tree, violations = (
                self.scope_postprocess_service.extend_child_scopes(
                    self.tree_to_flat(copy.deepcopy(compare_tree)), token_index_dict
                )
            )
            if violations == 0:
                combo_trees.append(compare_tree)
        return combo_trees

    def get_scope_combinations_v1(self, ref_doc_edit_id, comp_doc_edit_id, tokens):
        ref_doc_edit = self.get_scope_tree_by_document_edit_id(ref_doc_edit_id)
        comp_doc_edit = self.get_scope_tree_by_document_edit_id(comp_doc_edit_id)

        ambiguous_scopes = self.__get_ambiguous_subtrees(ref_doc_edit, comp_doc_edit)

        token_index_dict = dict()
        for token in tokens:
            token_index_dict[token["document_index"]] = token["id"]

        all_combinations = []
        for r in range(1, len(ambiguous_scopes)):
            all_combinations.extend(itertools.combinations(ambiguous_scopes, r))

        all_combinations = [list(comb) for comb in all_combinations]

        combo_trees = []
        for combination in all_combinations:
            invalid_combination = False
            compare_tree = copy.deepcopy(comp_doc_edit)
            for scope in combination:
                parent = self.__get_scope_in_tree(
                    compare_tree, scope["parent_scope_id"]
                )
                new_children = []
                for child in parent["children"]:
                    # case 1: child is completely inside scope => remove child
                    if (
                        child["token_start"]["document_index"]
                        >= scope["token_start"]["document_index"]
                        and child["token_end"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        continue

                    # case 2: child starts inside scope => adjust start
                    elif (
                        scope["token_start"]["document_index"]
                        <= child["token_start"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        child["token_start"]["document_index"] = (
                            scope["token_end"]["document_index"] + 1
                        )
                        child["token_start"]["id"] = token_index_dict[
                            child["token_start"]["document_index"]
                        ]
                        child_flat = self.tree_to_flat(child)
                        for child_child in child_flat:
                            # new scope completely covers existing child_child => discard combination
                            if (
                                child_child["token_end"]["document_index"]
                                < child["token_start"]["document_index"]
                            ):
                                invalid_combination = True
                                break
                        new_children.append(child)

                    # case 3: scope is completely inside child => remove child
                    elif (
                        child["token_start"]["document_index"]
                        <= scope["token_start"]["document_index"]
                        and child["token_end"]["document_index"]
                        >= scope["token_end"]["document_index"]
                    ):
                        continue

                    # case 4: child ends inside scope => adjust end
                    elif (
                        scope["token_start"]["document_index"]
                        <= child["token_end"]["document_index"]
                        <= scope["token_end"]["document_index"]
                    ):
                        child["token_end"]["document_index"] = (
                            scope["token_start"]["document_index"] - 1
                        )
                        child["token_end"]["id"] = token_index_dict[
                            child["token_end"]["document_index"]
                        ]

                        child_flat = self.tree_to_flat(child)
                        for child_child in child_flat:
                            # new scope completely covers existing child_child => discard combination
                            if (
                                child_child["token_start"]["document_index"]
                                > child["token_end"]["document_index"]
                            ):
                                invalid_combination = True
                                break
                        new_children.append(child)
                    else:
                        new_children.append(child)

                    if invalid_combination:
                        break
                if invalid_combination:
                    break
                parent["children"] = new_children
                parent["children"].append(scope)
            if not invalid_combination:
                compare_tree, _ = self.scope_postprocess_service.extend_child_scopes(
                    self.tree_to_flat(compare_tree), token_index_dict
                )
                combo_trees.append(compare_tree)
        return combo_trees

    def tree_to_flat(self, tree):
        scopes = []

        def traverse(cur_scope):
            scopes.append(cur_scope)

            for child in cur_scope.get("children", []):
                traverse(child)

        traverse(tree)
        return scopes

    def scopes_to_output(self, scopes):
        return [
            {
                "id": scope["id"],
                "parent_scope_id": scope["parent_scope_id"],
                "startTokenDocumentIndex": scope["token_start"]["document_index"],
                "endTokenDocumentIndex": scope["token_end"]["document_index"],
                "scope_type": scope["schema_scope"]["type"],
            }
            for scope in scopes
        ]

    def rec_to_tree(self, flat):
        id_to_scope = {}
        for scope in flat:
            scope["children"] = []
            id_to_scope[scope["id"]] = scope

        root = None
        for scope in id_to_scope.values():
            parent_id = scope.get("parent_scope_id")
            if parent_id is not None and parent_id in id_to_scope:
                id_to_scope[parent_id]["children"].append(scope)
            else:
                root = scope  # No parent = root
        return root

    def delete_scope_tree(self, document_edit_id):
        return self.__scope_repository.delete_scope_tree(document_edit_id)

    def get_leafs_by_document_edit_id(self, document_edit_id):
        scope_list = self.get_scope_list_by_document_edit_id(document_edit_id)
        parent_ids = [scope["parent_scope_id"] for scope in scope_list]
        leafs = [leaf for leaf in scope_list if leaf["id"] not in parent_ids]
        return leafs


scope_service = ScopeService(
    ScopeRepository(),
    scope_postprocess_service,
    token_service,
    schema_service,
    schema_scope_service,
    document_recommendation_service,
)
