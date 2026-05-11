"""`walk_nodes`: traverse an AAS v3 Submodel JSON and emit a flat node graph."""

from __future__ import annotations

from typing import Any

from idta_smt_walker.helpers import (
    LEAF_SME_TYPES,
    extract_cardinality,
    extract_semantic_id,
    normalize_model_type,
)
from idta_smt_walker.models import Event, Node, WalkResult


def walk_nodes(
    submodel_json: dict[str, Any],
    *,
    template_node_prefix: str = "",
) -> WalkResult:
    """Walk an AAS v3 Submodel JSON exhaustively with path-based identity.

    Args:
        submodel_json: A parsed JSON document. Either the AAS Environment shape
            with a top-level ``submodels`` array (the first submodel is walked),
            or a direct Submodel object.
        template_node_prefix: Optional prefix prepended to every
            ``template_node_id``. Use this to disambiguate node ids across
            multiple walked submodels, e.g. ``"IDTA_02006@3.0.1:"``.

    Returns:
        A :class:`WalkResult` with ``nodes`` (a flat ordered list of
        :class:`Node` records) and ``events`` (a structural diagnostic event log).
    """
    node_dicts: list[dict[str, Any]] = []
    event_dicts: list[dict[str, Any]] = []

    if isinstance(submodel_json, dict) and "submodels" in submodel_json:
        candidates = submodel_json["submodels"]
        if not candidates:
            return WalkResult(
                nodes=[],
                events=[Event(event="no_submodels_in_root", json_path="$")],
            )
        sm = candidates[0]
    else:
        sm = submodel_json

    def emit(
        *,
        path: str,
        elem: dict[str, Any],
        parent_path: str | None,
        json_path: str,
        is_list_prototype: bool = False,
    ) -> None:
        sem_id, supp_ids = extract_semantic_id(elem)
        cardinality, cardinality_raw = extract_cardinality(elem)
        node_dicts.append(
            {
                "template_node_id": f"{template_node_prefix}{path}",
                "aas_path": path,
                "parent_path": parent_path,
                "json_path": json_path,
                "id_short": elem.get("idShort"),
                "sme_type": normalize_model_type(elem),
                "semantic_id": sem_id,
                "supplemental_semantic_ids": supp_ids,
                "value_type": elem.get("valueType"),
                "cardinality_from_json": cardinality,
                "cardinality_qualifier_raw": cardinality_raw,
                "is_list_prototype": is_list_prototype,
            }
        )

    def child_path(parent_path: str, child: dict[str, Any], index: int) -> str:
        id_short = child.get("idShort")
        if id_short:
            return f"{parent_path}/{id_short}"
        return f"{parent_path}/[{index}]"

    def visit_at_path(
        elem: Any,
        *,
        path: str,
        parent_path: str | None,
        json_path: str,
        is_list_prototype: bool = False,
    ) -> None:
        if not isinstance(elem, dict):
            event_dicts.append(
                {
                    "event": "non_object_child",
                    "json_path": json_path,
                    "type": type(elem).__name__,
                }
            )
            return

        emit(
            path=path,
            elem=elem,
            parent_path=parent_path,
            json_path=json_path,
            is_list_prototype=is_list_prototype,
        )
        sme_type = normalize_model_type(elem)

        if sme_type == "Submodel":
            for i, child in enumerate(elem.get("submodelElements") or []):
                if not isinstance(child, dict):
                    event_dicts.append(
                        {
                            "event": "non_object_child",
                            "json_path": f"{json_path}.submodelElements[{i}]",
                        }
                    )
                    continue
                visit_at_path(
                    child,
                    path=child_path(path, child, i),
                    parent_path=path,
                    json_path=f"{json_path}.submodelElements[{i}]",
                )
        elif sme_type == "SubmodelElementCollection":
            for i, child in enumerate(elem.get("value") or []):
                if not isinstance(child, dict):
                    event_dicts.append(
                        {
                            "event": "non_object_child",
                            "json_path": f"{json_path}.value[{i}]",
                        }
                    )
                    continue
                visit_at_path(
                    child,
                    path=child_path(path, child, i),
                    parent_path=path,
                    json_path=f"{json_path}.value[{i}]",
                )
        elif sme_type == "SubmodelElementList":
            value = elem.get("value") or []
            if not value:
                event_dicts.append(
                    {
                        "event": "list_without_prototype",
                        "json_path": json_path,
                        "list_path": path,
                    }
                )
                return
            if len(value) > 1:
                event_dicts.append(
                    {
                        "event": "list_multiple_values_collapsed_to_prototype",
                        "json_path": json_path,
                        "list_path": path,
                        "value_count": len(value),
                    }
                )
            prototype = value[0]
            visit_at_path(
                prototype,
                path=f"{path}/*",
                parent_path=path,
                json_path=f"{json_path}.value[0]",
                is_list_prototype=True,
            )
        elif sme_type == "Entity":
            for i, child in enumerate(elem.get("statements") or []):
                if not isinstance(child, dict):
                    event_dicts.append(
                        {
                            "event": "non_object_child",
                            "json_path": f"{json_path}.statements[{i}]",
                        }
                    )
                    continue
                visit_at_path(
                    child,
                    path=child_path(path, child, i),
                    parent_path=path,
                    json_path=f"{json_path}.statements[{i}]",
                )
        elif sme_type == "AnnotatedRelationshipElement":
            for i, child in enumerate(elem.get("annotations") or []):
                if not isinstance(child, dict):
                    event_dicts.append(
                        {
                            "event": "non_object_child",
                            "json_path": f"{json_path}.annotations[{i}]",
                        }
                    )
                    continue
                visit_at_path(
                    child,
                    path=child_path(path, child, i),
                    parent_path=path,
                    json_path=f"{json_path}.annotations[{i}]",
                )
        elif sme_type not in LEAF_SME_TYPES:
            event_dicts.append(
                {
                    "event": "walker_unknown_shape",
                    "json_path": json_path,
                    "sme_type": sme_type,
                    "path": path,
                }
            )

    root_id = sm.get("idShort") if isinstance(sm, dict) else None
    if not root_id:
        event_dicts.append({"event": "submodel_without_idShort", "json_path": "$"})
        root_id = "UnnamedSubmodel"
    visit_at_path(sm, path=f"/{root_id}", parent_path=None, json_path="$")

    return WalkResult(
        nodes=[Node.model_validate(d) for d in node_dicts],
        events=[Event.model_validate(d) for d in event_dicts],
    )
