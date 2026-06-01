from app.api.v1.endpoints.operators import (
    get_operator_detail_by_name,
    list_operators,
    recommend_operator_categories,
)
from app.api.v1.errors import ValidationBizError
from app.core.container import container
from app.schemas.operator import OperatorCategoryRecommendationRequest


class StubOperatorRegistry:
    def __init__(self):
        self.details = {
            "Text2MultiHopQAGenerator": {
                "node": 1,
                "name": "Text2MultiHopQAGenerator",
                "type": {"level_1": "core_text", "level_2": "generate"},
                "allowed_prompts": ["Text2MultiHopQAGeneratorPrompt"],
                "description": "qa generator",
                "parameter": {
                    "init": [
                        {"name": "llm_serving", "default_value": None, "kind": "POSITIONAL_OR_KEYWORD"},
                        {"name": "prompt_template", "default_value": None, "kind": "POSITIONAL_OR_KEYWORD"},
                    ],
                    "run": [
                        {"name": "storage", "default_value": None, "kind": "POSITIONAL_OR_KEYWORD"},
                        {"name": "input_key", "default_value": "cleaned_chunk", "kind": "POSITIONAL_OR_KEYWORD"},
                        {"name": "output_key", "default_value": "qa_pairs", "kind": "POSITIONAL_OR_KEYWORD"},
                    ],
                },
                "required": "",
                "depends_on": [],
                "mode": "row",
            },
            "GeneralFilter": {
                "node": 2,
                "name": "GeneralFilter",
                "type": {"level_1": "core_text", "level_2": "filter"},
                "allowed_prompts": [],
                "description": "rule filter",
                "parameter": {
                    "init": [
                        {"name": "filter_rules", "default_value": None, "kind": "POSITIONAL_OR_KEYWORD"},
                    ],
                    "run": [
                        {"name": "storage", "default_value": None, "kind": "POSITIONAL_OR_KEYWORD"},
                    ],
                },
                "required": "",
                "depends_on": [],
                "mode": "row",
            },
        }

    def get_op_list(self, lang="zh"):
        return [
            {
                "name": detail["name"],
                "type": detail["type"],
                "allowed_prompts": detail["allowed_prompts"],
                "description": detail["description"],
            }
            for detail in self.details.values()
        ]

    def dump_ops_to_json(self, lang="zh"):
        return {"core_text": list(self.details.values())}


def test_list_operators_requires_category_with_recovery_hint(monkeypatch):
    monkeypatch.setattr(container, "operator_registry", StubOperatorRegistry())

    try:
        list_operators(category=None, lang="zh")
    except ValidationBizError as exc:
        assert exc.code == 40010
        assert "valid_categories" in exc.data
        assert "list_operator_categories" in exc.data["next_action"]
    else:
        raise AssertionError("Expected ValidationBizError")


def test_get_operator_detail_includes_agent_tips(monkeypatch):
    monkeypatch.setattr(container, "operator_registry", StubOperatorRegistry())

    resp = get_operator_detail_by_name("Text2MultiHopQAGenerator", lang="zh")
    data = resp.data
    assert data["field_binding_hint"]
    assert any("list_serving" in tip for tip in data["agent_tips"])
    assert any("suggested_fields" in tip for tip in data["agent_tips"])
    assert "top-level category 'core_text'" in data["mcp_context_hint"]


def test_recommend_operator_categories_returns_bounded_suggestions(monkeypatch):
    monkeypatch.setattr(container, "operator_registry", StubOperatorRegistry())

    resp = recommend_operator_categories(
        OperatorCategoryRecommendationRequest(
            task_description="Generate multi-hop QA from text chunks and filter low-score rows",
            dataset_columns=["chunk", "source"],
            max_categories=2,
        )
    )
    data = resp.data
    assert len(data["recommended_categories"]) <= 2
    assert data["recommended_categories"][0]["category"] == "core_text"
    assert data["query_budget"]["max_category_queries"] == 2
