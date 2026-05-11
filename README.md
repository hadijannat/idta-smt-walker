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

```bash
pip install idta-smt-walker
```

Requires Python 3.11+ and depends on `pydantic>=2.6`.

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

If you use this software, please cite it via the metadata in [`CITATION.cff`](CITATION.cff). Once a Zenodo DOI is assigned it will be included there as well.

## License

[MIT](LICENSE)
