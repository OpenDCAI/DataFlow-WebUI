---
name: core_text
description: >-
  Reference documentation for DataFlow's core_text operators — 8 generators,
  3 filters, 2 refiners and 5 evaluators. Read by generating-dataflow-pipeline
  when a task needs an operator beyond the six core primitives. This is a
  reference package, not a workflow: it is consulted, never invoked directly.
---

# core_text operator reference

Per-operator API documentation for DataFlow's `core_text` family. Consult it when
you need an operator's exact constructor and `run()` signature, its real
row-processing behaviour, or the mistakes that break it.

**Do not invoke this as a skill.** There is no workflow here. The
`generating-dataflow-pipeline` skill reads these files when it needs an operator
beyond its six core primitives.

## Layout

```
core_text/<category>/<operator>/
├── SKILL.md            English reference: constructor, run(), execution logic,
│                       mandatory rules, return-value semantics
├── SKILL_zh.md         Chinese translation
└── examples/
    ├── good.md         Best-practice pipeline usage
    └── bad.md          Common mistakes and how they fail
```

## What is documented

| Category | Path | Operators |
| --- | --- | --- |
| Generate | `generate/` | `PromptedGenerator`, `FormatStrPromptedGenerator`, `Text2MultiHopQAGenerator`, `BenchAnswerGenerator`, `ChunkedPromptedGenerator`, `EmbeddingGenerator`, `RandomDomainKnowledgeRowGenerator`, `RetrievalGenerator` |
| Filter | `filter/` | `GeneralFilter`, `KCenterGreedyFilter`, `PromptedFilter` |
| Refine | `refine/` | `PandasOperator`, `PromptedRefiner` |
| Eval | `eval/` | `BenchDatasetEvaluator`, `BenchDatasetEvaluatorQuestion`, `PromptedEvaluator`, `Text2QASampleEvaluator`, `UnifiedBenchDatasetEvaluator` |

## How to use it

1. Find the operator's directory under its category.
2. Read its `SKILL.md` for the authoritative signature.
3. Check that operator's `bad.md` example before writing code — it documents the
   failure modes that come up most often.

## Accuracy and scope

These are **static reference docs**, aligned to a specific DataFlow version
(recorded in `VERSION.md` in this directory). They are not a live query.

When an MCP server is available, `get_operator_detail_by_name` is authoritative:
it reflects the operators actually installed. Prefer it, and treat a
disagreement with these files as this reference being out of date.

## Adding an operator

1. Create `core_text/<category>/<operator-slug>/` containing `SKILL.md`, its
   `SKILL_zh.md` translation, plus `good.md` and `bad.md` under `examples/`.
2. Add the operator to the category table above. Add a rule to
   `../generating-dataflow-pipeline/SKILL.md` only when it changes operator
   selection policy; the planner reads this index on demand.
