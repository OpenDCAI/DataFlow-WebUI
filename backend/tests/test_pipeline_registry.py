"""Contract tests for the current file-backed PipelineRegistry API.

Execution records belong to TaskRegistry.  PipelineRegistry only manages
pipeline definitions and validates their configuration before persistence.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.container import container
from app.services.pipeline_registry import PipelineRegistry


class _DatasetRegistry:
    def get(self, dataset_id):
        return {"id": dataset_id} if dataset_id == "dataset-1" else None

    def get_columns(self, dataset_id):
        return ["text"] if dataset_id == "dataset-1" else []


@pytest.fixture
def pipeline_registry(tmp_path):
    original_dataset_registry = container.dataset_registry
    original_operator_registry = container.operator_registry
    original_serving_registry = container.serving_registry
    container.dataset_registry = _DatasetRegistry()
    container.operator_registry = SimpleNamespace(get_op_details=lambda *_args, **_kwargs: None)
    container.serving_registry = None

    registry_path = tmp_path / "pipelines.json"
    try:
        registry = PipelineRegistry(path=str(registry_path))
        yield registry, registry_path
    finally:
        container.dataset_registry = original_dataset_registry
        container.operator_registry = original_operator_registry
        container.serving_registry = original_serving_registry


@pytest.fixture
def pipeline_payload():
    return {
        "name": "Test pipeline",
        "config": {
            "file_path": "",
            "input_dataset": "dataset-1",
            "operators": [],
        },
        "tags": ["test"],
    }


def test_constructor_uses_the_requested_registry_path(pipeline_registry):
    registry, registry_path = pipeline_registry

    assert registry.path == str(registry_path)
    assert registry_path.is_file()


def test_create_and_get_pipeline_return_current_mapping_contract(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry

    created = registry.create_pipeline(pipeline_payload)
    fetched = registry.get_pipeline(created["id"])

    assert created["id"]
    assert created["name"] == "Test pipeline"
    assert created["config"]["input_dataset"] == "dataset-1"
    assert created["status"] == "queued"
    assert fetched == created


def test_create_rejects_a_missing_dataset(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry
    pipeline_payload["config"]["input_dataset"] = "missing"

    with pytest.raises(ValueError, match="Invalid pipeline configuration"):
        registry.create_pipeline(pipeline_payload)


def test_update_preserves_identity_and_updates_the_requested_fields(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry
    created = registry.create_pipeline(pipeline_payload)

    updated = registry.update_pipeline(
        created["id"],
        {"name": "Renamed", "tags": ["updated"]},
    )

    assert updated["id"] == created["id"]
    assert updated["name"] == "Renamed"
    assert updated["tags"] == ["updated"]
    assert updated["status"] == "queued"


def test_update_normalizes_and_persists_pipeline_name(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry
    created = registry.create_pipeline(pipeline_payload)

    updated = registry.update_pipeline(created["id"], {"name": "  Renamed pipeline  "})

    assert updated["name"] == "Renamed pipeline"
    assert registry.get_pipeline(created["id"])["name"] == "Renamed pipeline"


def test_update_rejects_an_empty_pipeline_name(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry
    created = registry.create_pipeline(pipeline_payload)

    with pytest.raises(ValueError, match="name cannot be empty"):
        registry.update_pipeline(created["id"], {"name": "   "})


def test_update_nonexistent_pipeline_fails(pipeline_registry):
    registry, _ = pipeline_registry

    with pytest.raises(ValueError, match="not found"):
        registry.update_pipeline("missing", {"name": "Nope"})


def test_list_and_delete_pipelines(pipeline_registry, pipeline_payload):
    registry, _ = pipeline_registry
    first = registry.create_pipeline(pipeline_payload)
    second = registry.create_pipeline({**pipeline_payload, "name": "Second"})

    assert {item["id"] for item in registry.list_pipelines()} == {first["id"], second["id"]}
    assert registry.delete_pipeline(first["id"]) is True
    assert registry.get_pipeline(first["id"]) is None
    assert registry.delete_pipeline(first["id"]) is False
