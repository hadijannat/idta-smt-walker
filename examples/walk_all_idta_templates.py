"""Walk every IDTA Submodel Template JSON in a local IDTA repo clone.

Usage:
    python examples/walk_all_idta_templates.py /path/to/admin-shell-io/submodel-templates

Or set the IDTA_TEMPLATES_DIR environment variable to point at the local clone.

Reports total nodes, walker_unknown_shape events, list_without_prototype events,
and any new SME shapes across the corpus. This is the empirical coverage check
that backs the README claim of "131 IDTA templates, zero unknown SME shapes."
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from idta_smt_walker import LEAF_SME_TYPES, walk_nodes

KNOWN_CONTAINER_SHAPES = frozenset(
    {
        "Submodel",
        "SubmodelElementCollection",
        "SubmodelElementList",
        "Entity",
        "AnnotatedRelationshipElement",
    }
)


def walk_one(json_path: Path) -> dict:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"template": json_path.name, "status": "parse_error", "error": str(exc)}

    result = walk_nodes(data)
    sme_types = Counter(n.sme_type for n in result.nodes)
    event_kinds = Counter(e.event for e in result.events)
    new_shapes = sorted(set(sme_types) - LEAF_SME_TYPES - KNOWN_CONTAINER_SHAPES)
    return {
        "template": json_path.name,
        "status": "walked",
        "nodes": len(result.nodes),
        "walker_unknown_shape": event_kinds.get("walker_unknown_shape", 0),
        "list_without_prototype": event_kinds.get("list_without_prototype", 0),
        "new_sme_shapes": new_shapes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "templates_dir",
        nargs="?",
        type=Path,
        default=Path(os.environ.get("IDTA_TEMPLATES_DIR", "")),
        help="Path to a local clone of admin-shell-io/submodel-templates.",
    )
    args = parser.parse_args()

    if not args.templates_dir or not Path(args.templates_dir).exists():
        print(
            "error: provide a path to a local clone of\n"
            "       https://github.com/admin-shell-io/submodel-templates\n"
            "       or set IDTA_TEMPLATES_DIR.",
            file=sys.stderr,
        )
        return 2

    templates = sorted(Path(args.templates_dir).rglob("*Template*.json"))
    print(f"Found {len(templates)} IDTA template JSONs under {args.templates_dir}")

    results = [walk_one(p) for p in templates]
    walked = [r for r in results if r["status"] == "walked"]
    parse_errors = [r for r in results if r["status"] == "parse_error"]

    total_unknown = sum(r["walker_unknown_shape"] for r in walked)
    total_lwp = sum(r["list_without_prototype"] for r in walked)
    total_nodes = sum(r["nodes"] for r in walked)
    new_shapes_corpus = sorted({s for r in walked for s in r["new_sme_shapes"]})

    print()
    print(f"=== Coverage summary across {len(walked)} templates ===")
    print(f"  total nodes                          : {total_nodes}")
    print(f"  walker_unknown_shape events (total)  : {total_unknown}")
    print(f"  list_without_prototype events (total): {total_lwp}")
    print(f"  new SME shapes across full corpus    : {new_shapes_corpus}")
    if parse_errors:
        print(f"  parse errors                         : {len(parse_errors)}")
        for r in parse_errors[:5]:
            print(f"    {r['template']}: {r['error']}")

    return 0 if total_unknown == 0 and not parse_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
