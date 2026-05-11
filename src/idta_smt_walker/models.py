"""Pydantic v2 models for the public API of `idta-smt-walker`."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    """A single addressable node in a walked IDTA Submodel Template graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    template_node_id: str = Field(
        description="Unique node id: <template_node_prefix><aas_path>.",
    )
    aas_path: str = Field(
        description="Path-based identity, e.g. /DigitalNameplate/Markings.",
    )
    parent_path: str | None = Field(
        default=None,
        description="Path of the immediate parent node.",
    )
    json_path: str = Field(
        description="JSON-pointer-like path to the underlying element.",
    )
    id_short: str | None = Field(
        default=None,
        description="The idShort attribute of the element.",
    )
    sme_type: str = Field(
        description="Normalised SME type, e.g. Property, SubmodelElementCollection.",
    )
    semantic_id: str | None = Field(
        default=None,
        description="Primary semantic_id value (first key value).",
    )
    supplemental_semantic_ids: list[str] = Field(
        default_factory=list,
        description="Additional semantic_id values from supplementalSemanticIds.",
    )
    value_type: str | None = Field(
        default=None,
        description="JSON-encoded valueType, if present.",
    )
    cardinality_from_json: str | None = Field(
        default=None,
        description=(
            "Structured cardinality, normalised via CARDINALITY_MAP (e.g. 1, 0..1, 0..*, 1..*)."
        ),
    )
    cardinality_qualifier_raw: str | None = Field(
        default=None,
        description=(
            "Raw cardinality string as it appears in the source JSON. "
            "Preserves IDTA-spec drift between versions."
        ),
    )
    is_list_prototype: bool = Field(
        default=False,
        description="True if this node is the prototype slot of a SubmodelElementList.",
    )


class Event(BaseModel):
    """A structural diagnostic event emitted during the walk."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: str = Field(
        description=(
            "Event kind, e.g. list_without_prototype, walker_unknown_shape, "
            "non_object_child, no_submodels_in_root, submodel_without_idShort."
        ),
    )
    json_path: str = Field(
        description="JSON-pointer-like path where the event occurred.",
    )
    sme_type: str | None = Field(
        default=None,
        description="SME type, populated when the event refers to one.",
    )
    path: str | None = Field(
        default=None,
        description="aas_path of the affected node, when relevant.",
    )
    list_path: str | None = Field(
        default=None,
        description="aas_path of the enclosing SubmodelElementList, when relevant.",
    )
    value_count: int | None = Field(
        default=None,
        description="Value count, when the event reports one.",
    )
    type: str | None = Field(
        default=None,
        description="Python type name, for non_object_child events.",
    )
    error: str | None = Field(
        default=None,
        description="Error message, when the event reports one.",
    )


class WalkResult(BaseModel):
    """The result of walking a Submodel JSON: a flat node list plus event log."""

    model_config = ConfigDict(frozen=True)

    nodes: list[Node]
    events: list[Event]
