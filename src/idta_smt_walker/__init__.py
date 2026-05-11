"""idta-smt-walker: parse IDTA Submodel Template JSON into a flat node graph.

Public API:
    walk_nodes(submodel_json, *, template_node_prefix="") -> WalkResult
    Node, Event, WalkResult                                 (Pydantic v2 models)
    LEAF_SME_TYPES, CARDINALITY_MAP                         (constants)
    extract_semantic_id, extract_cardinality, normalize_model_type
                                                            (helpers)
"""

from __future__ import annotations

from idta_smt_walker.helpers import (
    CARDINALITY_MAP,
    LEAF_SME_TYPES,
    extract_cardinality,
    extract_semantic_id,
    normalize_model_type,
)
from idta_smt_walker.models import Event, Node, WalkResult
from idta_smt_walker.walker import walk_nodes

try:
    from idta_smt_walker._version import version as __version__
except ImportError:  # pragma: no cover - only hit on editable installs without scm tags
    __version__ = "0.0.0+unknown"

__all__ = [
    "CARDINALITY_MAP",
    "LEAF_SME_TYPES",
    "Event",
    "Node",
    "WalkResult",
    "__version__",
    "extract_cardinality",
    "extract_semantic_id",
    "normalize_model_type",
    "walk_nodes",
]
