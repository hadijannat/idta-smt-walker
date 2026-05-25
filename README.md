# idta-smt-walker

> Parse any IDTA Submodel Template JSON into a flat list of typed nodes with path-based identity.

[![CI](https://github.com/hadijannat/idta-smt-walker/actions/workflows/ci.yml/badge.svg)](https://github.com/hadijannat/idta-smt-walker/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-005571)](https://docs.pydantic.dev/2.0/)

## What it does

`idta-smt-walker` takes any [Asset Administration Shell (AAS)](https://industrialdigitaltwin.org/) Submodel Template JSON — for example one of the templates published by the Industrial Digital Twin Association (IDTA) at [admin-shell-io/submodel-templates](https://github.com/admin-shell-io/submodel-templates) — and emits a flat ordered list of typed nodes with:

- path-based identity (`/Submodel/Section/Element`)
- cardinality, both the structured form (`1`, `0..1`, `0..*`, `1..*`) and the raw qualifier string
- semantic id (primary plus any supplemental ids)
- SME (Submodel Element) type
- a structural-event log for non-standard shapes (`list_without_prototype`, `walker_unknown_shape`, etc.)

The output is intended as a stable substrate for downstream tools such as constraint validators, prompt-anchored LLM extractors, and breaking-change diff tools across IDTA spec versions.

## Design: a flat node graph

`walk_nodes` emits a flat ordered list of path-identified nodes rather than a tree of typed object-oriented instance classes. The contrasting design, generating one Python class per Submodel Element type, is taken by [`rwth-iat/aas-submodel-template-to-py`](https://github.com/rwth-iat/aas-submodel-template-to-py) (see Related work). That approach binds the consumer to a generated class hierarchy that must be regenerated whenever a Submodel Template changes. The flat node graph keeps a single uniform node type and moves all structure into the `aas_path` string, so the same code reads every Submodel Template.

Path-based identity is what makes the substrate composable downstream:

- **Constraint validators** key cardinality and semantic-id rules to `aas_path`, so a rule references a stable string rather than a position in a class tree.
- **Prompt-anchored LLM extraction** uses the node graph as a bounded enumeration of the fields an extractor is allowed to populate. Each `aas_path` is a slot, and abstention is the absence of a value for a slot.
- **Breaking-change diffs** across IDTA spec versions reduce to a set difference over `aas_path` values plus a comparison of `cardinality_from_json` and `semantic_id` per shared path. The retained `cardinality_qualifier_raw` field preserves the verbatim source string so qualifier drift between versions stays visible.

### Downstream composition

The companion repository [`idta-smt-extraction-prompts`](https://github.com/hadijannat/idta-smt-extraction-prompts) consumes this node graph as the bounded template node graph that constrains LLM emission. The walker defines which paths exist for a given Submodel Template, and the extractor populates values only for those paths. The two repositories together back an ETFA 2026 academic paper on schema-constrained extraction.

### The structural-event log

Every walk returns a `WalkResult` carrying both `nodes` and `events`. Events are non-fatal structural observations. The walker logs them rather than raising, so a walk over a malformed or non-standard Submodel Template still returns a complete node graph alongside a diagnostic trail. A `SubmodelElementList` with an empty `value`, for example, records a `list_without_prototype` event and continues. An unrecognised Submodel Element type records a `walker_unknown_shape` event.

This design is how the coverage claim below is measured. Walking all 131 templates and counting `walker_unknown_shape` events yields the **0 unknown shapes** result. A non-zero count would name the template and the path where the walker met a shape outside its known leaf and container sets.

## Verified coverage

Empirically verified on **131 IDTA Submodel Template JSONs** (across 47+ template categories, including 02002 Contact Information, 02003 Technical Data, 02004 Handover Documentation, 02006 Digital Nameplate, 02011 Hierarchical Structures, 02017 Asset Interfaces, 02021 Power Drive Trains, 02023 Carbon Footprint, 02050 Purchase Order, and AAS Metamodel V3.1 variants):

| Metric | Value |
|---|---|
| Templates walked | **131** |
| Total nodes emitted | **11,124** |
| `walker_unknown_shape` events | **0** |
| New SME shapes beyond known set | **0** |
| Parse errors | 0 |

Re-run this verification at any time:

```bash
git clone https://github.com/admin-shell-io/submodel-templates ~/idta-templates
python examples/walk_all_idta_templates.py ~/idta-templates
```

See [`examples/walk_all_idta_templates.py`](examples/walk_all_idta_templates.py).

## Installation

Install from source:

```bash
pip install git+https://github.com/hadijannat/idta-smt-walker
```

Requires Python 3.11+ and depends on `pydantic>=2.6`. A PyPI release is planned.

## Quick start

```python
import json
from pathlib import Path
from idta_smt_walker import walk_nodes

data = json.loads(Path("IDTA_02006-3-0-1_Template_Digital_Nameplate.json").read_text())

result = walk_nodes(data)

print(f"{len(result.nodes)} nodes, {len(result.events)} events")
for node in result.nodes[:5]:
    print(f"  {node.aas_path}  ({node.sme_type}, cardinality={node.cardinality_from_json})")
```

To disambiguate node ids across multiple walked submodels, pass a `template_node_prefix`:

```python
result = walk_nodes(data, template_node_prefix="IDTA_02006@3.0.1:")
# result.nodes[0].template_node_id == "IDTA_02006@3.0.1:/DigitalNameplate"
```

## Public API

All public types are [Pydantic v2](https://docs.pydantic.dev/2.0/) models. They are frozen and reject extra fields.

```python
from idta_smt_walker import walk_nodes, Node, Event, WalkResult, LEAF_SME_TYPES

result: WalkResult = walk_nodes(submodel_json, template_node_prefix="")
result.nodes   # list[Node]
result.events  # list[Event]
```

### `Node`

| Field | Type | Description |
|---|---|---|
| `template_node_id` | `str` | Unique id: `<template_node_prefix><aas_path>`. |
| `aas_path` | `str` | Path-based identity, e.g. `/DigitalNameplate/Markings`. |
| `parent_path` | `str \| None` | Path of the immediate parent. |
| `json_path` | `str` | JSON-pointer-like path to the underlying element. |
| `id_short` | `str \| None` | The `idShort` attribute. |
| `sme_type` | `str` | Normalised SME type (e.g. `Property`, `SubmodelElementCollection`). |
| `semantic_id` | `str \| None` | Primary `semantic_id` value. |
| `supplemental_semantic_ids` | `list[str]` | Additional values from `supplementalSemanticIds`. |
| `value_type` | `str \| None` | JSON-encoded `valueType`. |
| `cardinality_from_json` | `str \| None` | Structured cardinality (`1`, `0..1`, `0..*`, `1..*`). |
| `cardinality_qualifier_raw` | `str \| None` | Raw cardinality string as it appears in the source JSON. |
| `is_list_prototype` | `bool` | True if this node is the prototype slot of a `SubmodelElementList`. |

### `Event`

`event` is one of:

| Event kind | Meaning |
|---|---|
| `list_without_prototype` | `SubmodelElementList` with empty `value` (walker skips the prototype). |
| `list_multiple_values_collapsed_to_prototype` | `SubmodelElementList` with multiple values (walker uses the first as prototype). |
| `walker_unknown_shape` | SME type not in the known leaf or container set. |
| `non_object_child` | Encountered a non-dict child where an object was expected. |
| `no_submodels_in_root` | Environment shape with empty `submodels` array. |
| `submodel_without_idShort` | Submodel object missing `idShort`. |

## Related work

`idta-smt-walker` complements existing AAS-Python tooling rather than replacing it:

- [`aas-core-works/aas-core3.0-python`](https://github.com/aas-core-works/aas-core3.0-python) — codegen-driven SDK for **AAS v3 instances** (de/serialisation plus verification). `idta-smt-walker` operates on the same JSON but emits a flat node list rather than typed instance objects.
- [`eclipse-basyx/basyx-python-sdk`](https://github.com/eclipse-basyx/basyx-python-sdk) — reference Python SDK for AAS v3.
- [`rwth-iat/aas-submodel-template-to-py`](https://github.com/rwth-iat/aas-submodel-template-to-py) (Garmaev et al., GPL-3.0, RWTH IAT) — generates **typed Python classes** from IDTA Submodel Templates. Different abstraction (object-oriented) and different licence (GPL-3.0 vs MIT here).

## Citation

This software is archived on Zenodo under the concept DOI [10.5281/zenodo.20127614](https://doi.org/10.5281/zenodo.20127614). The machine-readable metadata is in [`CITATION.cff`](CITATION.cff).

Plaintext:

> Khori Jannatabadi, M. H. (2026). *idta-smt-walker* (Version 0.1.0) [Computer software]. https://doi.org/10.5281/zenodo.20127614

BibTeX:

```bibtex
@software{khorijannatabadi_idta_smt_walker_2026,
  author    = {Khori Jannatabadi, Mohammad Hadi},
  title     = {idta-smt-walker},
  year      = {2026},
  version   = {0.1.0},
  doi       = {10.5281/zenodo.20127614},
  url       = {https://github.com/hadijannat/idta-smt-walker}
}
```

## License

[MIT](LICENSE)
