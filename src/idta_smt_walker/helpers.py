"""Pure helper functions used by `walk_nodes`."""

from __future__ import annotations

from typing import Any

LEAF_SME_TYPES: frozenset[str] = frozenset(
    {
        "Property",
        "MultiLanguageProperty",
        "File",
        "Range",
        "Blob",
        "ReferenceElement",
        "RelationshipElement",
        "BasicEventElement",
        "Operation",
        "Capability",
    }
)
"""Submodel Element shapes that have no addressable children for traversal."""

CARDINALITY_MAP: dict[str, str] = {
    "One": "1",
    "ZeroToOne": "0..1",
    "ZeroToMany": "0..*",
    "OneToMany": "1..*",
}
"""IDTA SMT/Cardinality qualifier values mapped to their structured form."""


def normalize_model_type(elem: dict[str, Any]) -> str:
    """Return the Submodel Element type as a plain string.

    Accepts either the legacy AAS shape (``modelType`` is a dict with ``name``)
    or the AAS v3 shape (``modelType`` is a plain string).
    """
    mt = elem.get("modelType", "Unknown")
    if isinstance(mt, dict):
        return str(mt.get("name", "Unknown"))
    return str(mt)


def extract_semantic_id(elem: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Return (primary semantic_id, supplemental semantic_ids) from an AAS element.

    Primary is the ``value`` of the first key in ``semanticId.keys``.
    Supplemental are the first-key values of each ``supplementalSemanticIds`` entry.
    """
    sem = elem.get("semanticId") or {}
    primary: str | None = None
    if isinstance(sem, dict):
        keys = sem.get("keys") or []
        if keys and isinstance(keys[0], dict):
            v = keys[0].get("value")
            primary = str(v) if v is not None else None

    supps: list[str] = []
    for supp in elem.get("supplementalSemanticIds") or []:
        if not isinstance(supp, dict):
            continue
        keys = supp.get("keys") or []
        if keys and isinstance(keys[0], dict) and keys[0].get("value"):
            supps.append(str(keys[0]["value"]))
    return primary, supps


def extract_cardinality(elem: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return ``(structured_cardinality, raw_qualifier_string)`` for an element.

    Looks first at a direct ``cardinality`` field, then at ``SMT/Cardinality``
    qualifiers (identified by ``type`` or by the ``SubmodelTemplates/Cardinality``
    semantic id substring). Returns ``(None, None)`` if no cardinality info is
    present.

    The raw string is preserved verbatim so that IDTA-spec drift between versions
    remains visible to downstream tooling.
    """
    direct = elem.get("cardinality")
    if direct:
        return str(direct), str(direct)
    for qual in elem.get("qualifiers") or []:
        if not isinstance(qual, dict):
            continue
        q_type = str(qual.get("type") or "")
        sem_id, _ = extract_semantic_id(qual)
        if q_type == "SMT/Cardinality" or (sem_id and "SubmodelTemplates/Cardinality" in sem_id):
            raw = qual.get("value")
            if raw is not None:
                raw_s = str(raw)
                return CARDINALITY_MAP.get(raw_s, raw_s), raw_s
    return None, None
