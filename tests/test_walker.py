"""Unit tests for `walk_nodes`."""

from __future__ import annotations

from idta_smt_walker import walk_nodes


def _minimal_submodel() -> dict:
    return {
        "modelType": "Submodel",
        "idShort": "DigitalNameplate",
        "submodelElements": [
            {
                "modelType": "Property",
                "idShort": "URIOfTheProduct",
                "valueType": "xs:string",
                "qualifiers": [
                    {"type": "SMT/Cardinality", "value": "One"},
                ],
            },
            {
                "modelType": "SubmodelElementCollection",
                "idShort": "Markings",
                "value": [
                    {
                        "modelType": "Property",
                        "idShort": "Marking",
                        "valueType": "xs:string",
                    },
                ],
            },
        ],
    }


def test_walks_minimal_submodel_in_document_order() -> None:
    result = walk_nodes(_minimal_submodel())
    assert len(result.events) == 0
    paths = [n.aas_path for n in result.nodes]
    assert paths == [
        "/DigitalNameplate",
        "/DigitalNameplate/URIOfTheProduct",
        "/DigitalNameplate/Markings",
        "/DigitalNameplate/Markings/Marking",
    ]


def test_cardinality_extraction_from_qualifier() -> None:
    result = walk_nodes(_minimal_submodel())
    uri = next(n for n in result.nodes if n.aas_path == "/DigitalNameplate/URIOfTheProduct")
    assert uri.cardinality_from_json == "1"
    assert uri.cardinality_qualifier_raw == "One"


def test_template_node_prefix_is_prepended() -> None:
    result = walk_nodes(_minimal_submodel(), template_node_prefix="IDTA_02006@3.0.1:")
    root = result.nodes[0]
    assert root.template_node_id == "IDTA_02006@3.0.1:/DigitalNameplate"
    assert root.aas_path == "/DigitalNameplate"


def test_default_template_node_prefix_is_empty() -> None:
    result = walk_nodes(_minimal_submodel())
    assert result.nodes[0].template_node_id == "/DigitalNameplate"


def test_submodel_element_list_with_prototype() -> None:
    sm = {
        "modelType": "Submodel",
        "idShort": "Root",
        "submodelElements": [
            {
                "modelType": "SubmodelElementList",
                "idShort": "Items",
                "value": [
                    {"modelType": "Property", "idShort": "Item", "valueType": "xs:string"},
                ],
            },
        ],
    }
    result = walk_nodes(sm)
    paths = [n.aas_path for n in result.nodes]
    assert "/Root/Items" in paths
    assert "/Root/Items/*" in paths
    proto = next(n for n in result.nodes if n.aas_path == "/Root/Items/*")
    assert proto.is_list_prototype is True


def test_list_without_prototype_emits_event() -> None:
    sm = {
        "modelType": "Submodel",
        "idShort": "Root",
        "submodelElements": [
            {"modelType": "SubmodelElementList", "idShort": "EmptyList", "value": []},
        ],
    }
    result = walk_nodes(sm)
    assert any(e.event == "list_without_prototype" for e in result.events)


def test_unknown_sme_shape_emits_event() -> None:
    sm = {
        "modelType": "Submodel",
        "idShort": "Root",
        "submodelElements": [
            {"modelType": "NonStandardShape", "idShort": "Mystery"},
        ],
    }
    result = walk_nodes(sm)
    assert any(e.event == "walker_unknown_shape" for e in result.events)


def test_environment_wrapper_walks_first_submodel() -> None:
    env = {"submodels": [_minimal_submodel()]}
    result = walk_nodes(env)
    assert any(n.aas_path == "/DigitalNameplate" for n in result.nodes)


def test_empty_environment_emits_no_submodels_event() -> None:
    result = walk_nodes({"submodels": []})
    assert result.nodes == []
    assert result.events[0].event == "no_submodels_in_root"


def test_legacy_modeltype_dict_is_normalised() -> None:
    sm = {
        "modelType": {"name": "Submodel"},
        "idShort": "Root",
        "submodelElements": [
            {"modelType": {"name": "Property"}, "idShort": "P", "valueType": "xs:string"},
        ],
    }
    result = walk_nodes(sm)
    sme_types = {n.sme_type for n in result.nodes}
    assert sme_types == {"Submodel", "Property"}


def test_semantic_id_extraction() -> None:
    sm = {
        "modelType": "Submodel",
        "idShort": "Root",
        "semanticId": {"keys": [{"value": "https://example.org/Submodel"}]},
        "submodelElements": [
            {
                "modelType": "Property",
                "idShort": "P",
                "valueType": "xs:string",
                "semanticId": {"keys": [{"value": "https://example.org/Property"}]},
                "supplementalSemanticIds": [
                    {"keys": [{"value": "https://eclass.eu/12-34-56-78"}]},
                ],
            },
        ],
    }
    result = walk_nodes(sm)
    p = next(n for n in result.nodes if n.aas_path == "/Root/P")
    assert p.semantic_id == "https://example.org/Property"
    assert p.supplemental_semantic_ids == ["https://eclass.eu/12-34-56-78"]
