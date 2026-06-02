import pytest

from app.core.container import container
from app.services.dataset_registry import DatasetRegistry
from app.services.pipeline_registry import PipelineRegistry


@pytest.fixture
def validation_env(tmp_path):
    dataset_registry_path = tmp_path / "datasets.yaml"
    pipeline_registry_path = tmp_path / "pipelines.json"

    original_dataset_registry = container.dataset_registry
    original_operator_registry = container.operator_registry
    original_serving_registry = container.serving_registry

    container.dataset_registry = DatasetRegistry(path=str(dataset_registry_path), scan=False)

    sample_path = tmp_path / "sample.jsonl"
    sample_path.write_text('{"text": "hello", "url": "https://example.com"}\n', encoding='utf-8')
    dataset = container.dataset_registry.add_or_update(
        {
            "name": "sample",
            "root": str(sample_path),
            "pipeline": "test",
            "meta": {},
        }
    )

    class StubOperatorRegistry:
        def __init__(self):
            self.details = {
                "PromptedGenerator": {
                    "name": "PromptedGenerator",
                    "allowed_prompts": [],
                    "parameter": {
                        "init": [
                            {"name": "llm_serving"},
                            {"name": "system_prompt"},
                            {"name": "prompt_template"},
                        ],
                        "run": [
                            {"name": "storage", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "input_key", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "output_key", "kind": "POSITIONAL_OR_KEYWORD"},
                        ],
                    },
                },
                "Text2MultiHopQAGenerator": {
                    "name": "Text2MultiHopQAGenerator",
                    "allowed_prompts": ["Text2MultiHopQAGeneratorPrompt"],
                    "parameter": {
                        "init": [
                            {"name": "llm_serving"},
                            {"name": "prompt_template"},
                            {"name": "num_q"},
                        ],
                        "run": [
                            {"name": "storage", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "input_key", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "output_key", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "output_meta_key", "kind": "POSITIONAL_OR_KEYWORD"},
                        ],
                    },
                },
                "PandasOperator": {
                    "name": "PandasOperator",
                    "allowed_prompts": [],
                    "parameter": {
                        "init": [
                            {"name": "process_fn"},
                        ],
                        "run": [
                            {"name": "storage", "kind": "POSITIONAL_OR_KEYWORD"},
                            {"name": "output_key", "kind": "POSITIONAL_OR_KEYWORD"},
                        ],
                    },
                },
                "GeneralFilter": {
                    "name": "GeneralFilter",
                    "allowed_prompts": [],
                    "parameter": {
                        "init": [
                            {"name": "filter_rules"},
                        ],
                        "run": [
                            {"name": "storage", "kind": "POSITIONAL_OR_KEYWORD"},
                        ],
                    },
                },
            }

        def get_op_details(self, name, lang="zh"):
            return self.details.get(name)

        def get_op_list(self, lang="zh"):
            return [
                {
                    "name": detail["name"],
                    "type": {"level_1": "core_text", "level_2": "generate"},
                    "allowed_prompts": detail.get("allowed_prompts", []),
                    "description": detail.get("name", ""),
                }
                for detail in self.details.values()
            ]

    container.operator_registry = StubOperatorRegistry()

    class StubServingRegistry:
        def _get(self, serving_id):
            if serving_id == "serving_ok":
                return {"id": "serving_ok", "name": "serving_ok"}
            return None

    container.serving_registry = StubServingRegistry()

    registry = PipelineRegistry(path=str(pipeline_registry_path))
    registry.path = str(pipeline_registry_path)
    registry._write({"pipelines": {}})

    try:
        yield registry, dataset["id"]
    finally:
        container.dataset_registry = original_dataset_registry
        container.operator_registry = original_operator_registry
        container.serving_registry = original_serving_registry


def test_validate_pipeline_detects_missing_input_field(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "PromptedGenerator",
                    "params": {
                        "llm_serving": "serving_ok",
                        "system_prompt": "classify",
                        "input_key": "missing_field",
                        "output_key": "label",
                    },
                }
            ],
        }
    )

    assert result.valid is False
    issue = next(issue for issue in result.errors if issue.code == "missing_input_field")
    assert issue.field_name == "missing_field"
    assert issue.available_fields == ["text", "url"]
    assert issue.repair_hint



def test_validate_pipeline_suggests_similar_input_field(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "PromptedGenerator",
                    "params": {
                        "llm_serving": "serving_ok",
                        "system_prompt": "classify",
                        "input_key": "texts",
                        "output_key": "label",
                    },
                }
            ],
        }
    )

    issue = next(issue for issue in result.errors if issue.code == "missing_input_field")
    assert "text" in issue.suggested_fields
    assert "texts" in issue.repair_hint


def test_validate_pipeline_accepts_top_level_text_and_new_output(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "PromptedGenerator",
                    "params": {
                        "llm_serving": "serving_ok",
                        "system_prompt": "classify",
                        "input_key": "text",
                        "output_key": "label",
                    },
                }
            ],
        }
    )

    assert result.valid is True
    assert result.errors == []
    assert "label" in result.final_available_fields


def test_validate_pipeline_rejects_unknown_serving_and_prompt_class(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "Text2MultiHopQAGenerator",
                    "params": {
                        "llm_serving": {"id": "serving_missing"},
                        "prompt_template": "WrongPrompt",
                        "input_key": "text",
                        "output_key": "qa_pairs",
                        "output_meta_key": "qa_meta",
                    },
                }
            ],
        }
    )

    assert result.valid is False
    error_codes = {issue.code for issue in result.errors}
    assert "serving_not_found" in error_codes
    assert "invalid_prompt_template_class" in error_codes


def test_validate_pipeline_accepts_json_encoded_process_fn(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "PandasOperator",
                    "params": {
                        "process_fn": "[{\"code\": \"lambda df: df.rename(columns={'text': 'content'})\"}]",
                        "output_key": "content_frame",
                    },
                }
            ],
        }
    )

    assert result.valid is True
    assert result.errors == []


def test_validate_pipeline_rejects_invalid_dynamic_code_object(validation_env):
    registry, dataset_id = validation_env
    result = registry.validate_pipeline_config(
        {
            "file_path": "",
            "input_dataset": {"id": dataset_id},
            "operators": [
                {
                    "name": "GeneralFilter",
                    "params": {
                        "filter_rules": [{"type": "lambda"}],
                    },
                }
            ],
        }
    )

    assert result.valid is False
    assert any(issue.code == "invalid_dynamic_code_param" for issue in result.errors)


def test_operator_category_recommendation_heuristic(validation_env):
    registry, dataset_id = validation_env
    recommendation = container.operator_registry.get_op_list()
    assert recommendation

    from app.services.operator_category_guide import recommend_categories

    result = recommend_categories(
        task_description="请从 text 字段生成多跳 QA 对并过滤低质量结果",
        dataset_columns=["text", "url"],
        max_categories=2,
    )

    assert result["recommended_categories"][0]["category"] == "core_text"
    assert result["query_budget"]["max_category_queries"] == 2
