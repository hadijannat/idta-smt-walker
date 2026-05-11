"""Tests for the Pydantic v2 public-API models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from idta_smt_walker import Event, Node, WalkResult


def test_node_minimal_required_fields() -> None:
    n = Node(
        template_node_id="/Root",
        aas_path="/Root",
        json_path="$",
        sme_type="Submodel",
    )
    assert n.parent_path is None
    assert n.id_short is None
    assert n.supplemental_semantic_ids == []
    assert n.is_list_prototype is False


def test_node_is_frozen() -> None:
    n = Node(
        template_node_id="/Root",
        aas_path="/Root",
        json_path="$",
        sme_type="Submodel",
    )
    with pytest.raises(ValidationError):
        n.aas_path = "/Different"  # type: ignore[misc]


def test_node_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Node(
            template_node_id="/Root",
            aas_path="/Root",
            json_path="$",
            sme_type="Submodel",
            not_a_real_field="value",  # type: ignore[call-arg]
        )


def test_event_minimal_required_fields() -> None:
    e = Event(event="list_without_prototype", json_path="$.foo")
    assert e.path is None
    assert e.value_count is None


def test_event_is_frozen() -> None:
    e = Event(event="non_object_child", json_path="$.foo", type="str")
    with pytest.raises(ValidationError):
        e.event = "other"  # type: ignore[misc]


def test_walk_result_round_trip_via_json() -> None:
    nodes = [
        Node(
            template_node_id="/Root",
            aas_path="/Root",
            json_path="$",
            sme_type="Submodel",
        ),
    ]
    events = [Event(event="non_object_child", json_path="$.value[0]", type="str")]
    result = WalkResult(nodes=nodes, events=events)
    dumped = result.model_dump_json()
    restored = WalkResult.model_validate_json(dumped)
    assert restored.nodes[0].aas_path == "/Root"
    assert restored.events[0].event == "non_object_child"


def test_walk_result_with_empty_lists() -> None:
    result = WalkResult(nodes=[], events=[])
    assert result.nodes == []
    assert result.events == []
