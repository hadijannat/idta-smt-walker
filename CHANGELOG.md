# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation

- Expanded `README.md` with a "Design: a flat node graph" section covering the
  data-model rationale (path-identified nodes versus generated object-oriented
  instance classes), how the node graph composes into constraint validators,
  prompt-anchored LLM extraction, and breaking-change diffs, and how the
  structural-event log measures the zero-unknown-shapes coverage claim.
- Cross-linked the companion repository `idta-smt-extraction-prompts`, which
  consumes the node graph as the bounded template node graph that constrains
  LLM emission.
- Corrected the installation instruction to an honest from-source install
  (`pip install git+https://github.com/hadijannat/idta-smt-walker`). The package
  is not yet on PyPI.
- Replaced the placeholder citation note with a Citation section stating the
  Zenodo DOI `10.5281/zenodo.20127614`, a plaintext citation, and a BibTeX
  `@software` entry.

## [0.1.0] — 2026-05-11

### Added

- `walk_nodes(submodel_json, *, template_node_prefix="")` function. Traverses an
  AAS v3 Submodel JSON and returns a `WalkResult` with a flat ordered node list
  and a structural-event log.
- Pydantic v2 public-API models: `Node`, `Event`, `WalkResult` (all frozen,
  `extra="forbid"`).
- Helper functions: `extract_semantic_id`, `extract_cardinality`,
  `normalize_model_type`.
- Constants: `LEAF_SME_TYPES`, `CARDINALITY_MAP`.
- Example script `examples/walk_all_idta_templates.py` for empirical coverage
  verification across a local IDTA-templates clone.
- MIT licence, Zenodo-ready `CITATION.cff`.
- GitHub Actions CI matrix on Python 3.11 and 3.12: ruff lint + ruff format +
  mypy strict + pytest with coverage.

### Verified

- Walked 131 IDTA Submodel Template JSONs from
  [admin-shell-io/submodel-templates](https://github.com/admin-shell-io/submodel-templates)
  with 11,124 total nodes, zero `walker_unknown_shape` events, and zero new
  SME shapes beyond the documented leaf and container sets.

[Unreleased]: https://github.com/hadijannat/idta-smt-walker/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hadijannat/idta-smt-walker/releases/tag/v0.1.0
