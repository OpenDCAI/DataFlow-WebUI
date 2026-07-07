"""Pipeline compile-time key check.

Runs DataFlow's *real* ``PipelineABC.compile()`` key-integrity validation on a
pipeline that has already been assembled by the Ray executor (operators
instantiated, storage built). This is the same check DataFlow performs when a
hand-written pipeline calls ``pipeline.compile()``:

    for each operator, every ``input_*`` key must already exist in the
    accumulated key set (dataset columns + upstream ``output_*`` keys);
    otherwise ``compile()`` raises ``KeyError("Key Matching Error ...")``.

The WebUI executor previously ran ``operator.run(**run_params)`` directly with
no pre-check, so a broken key flow only surfaced as a mid-run crash. Calling
``compile_check`` before the run loop makes "only runnable pipelines run".

Why this does NOT execute the operators / call the LLM:
``compile()`` first replaces every ``OperatorABC`` attribute on the pipeline
with an ``AutoOP`` wrapper, then calls ``forward()``. ``AutoOP.run`` only
*records* an ``OPRuntime`` (operator + kwargs) — it never invokes the operator's
real logic. So ``forward()`` here just registers each op's key params; the
actual key-graph validation happens in ``_build_operator_nodes_graph``.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

from dataflow.pipeline import PipelineABC

from app.core.logger_setup import get_logger

logger = get_logger(__name__)


def _key_params(run_params: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only the params DataFlow's OperatorNode treats as keys.

    ``OperatorNode._get_keys_from_kwargs`` (dataflow/pipeline/nodes.py) only
    looks at kwargs named ``input_*`` / ``output_*`` with string values. We pass
    exactly those to ``AutoOP.run`` so the compile key graph matches what the
    real run would produce, and we omit everything else (``storage`` is supplied
    by ``forward``; other params would just bloat the bound signature).
    """
    out: Dict[str, Any] = {}
    for name, value in run_params.items():
        if name == "storage":
            continue
        if (name.startswith("input_") or name.startswith("output_")) and isinstance(value, str):
            out[name] = value
    return out


def compile_check(run_op: List[Tuple[Any, Dict[str, Any], str, str]], storage: Any) -> Dict[str, Any]:
    """Run DataFlow's compile() key validation on an assembled pipeline.

    Args:
        run_op: list of ``(operator_instance, run_params, op_name, op_key)`` as
            built by the Ray executor.
        storage: the ``FileStorage`` already pointing at the input dataset.

    Returns a dict:
        {"ok": bool, "detail": str, "errors": [ ... ], "skipped": bool}

    ``skipped=True`` (with ok=True) means the check could not run for an
    unexpected reason and was intentionally bypassed — the executor then
    proceeds as before rather than failing on an infrastructure issue.
    """
    if not run_op:
        return {"ok": True, "detail": "no operators", "errors": [], "skipped": False}

    # Snapshot key params per operator BEFORE building the pipeline, since the
    # executor mutates run_params["storage"] later.
    ops_and_keys: List[Tuple[Any, Dict[str, Any], str]] = [
        (operator, _key_params(run_params), op_name)
        for (operator, run_params, op_name, _op_key) in run_op
    ]

    class _ConfigPipeline(PipelineABC):
        def __init__(self, _storage, _ops_and_keys):
            super().__init__()
            self._df_storage = _storage
            self._ordered = []  # (attr_name, key_params)
            for idx, (operator, key_params, _op_name) in enumerate(_ops_and_keys):
                attr = f"_op_{idx}"
                # compile() scans vars(self) for OperatorABC instances and wraps
                # them into AutoOP, so the operator must live as an attribute.
                setattr(self, attr, operator)
                self._ordered.append((attr, key_params))

        def forward(self):
            for attr, key_params in self._ordered:
                op = getattr(self, attr)  # AutoOP wrapper at compile time
                op.run(storage=self._df_storage.step(), **key_params)

    try:
        # 用一个浅拷贝的 storage 做 compile，绝不触碰执行器真实的 storage —
        # FileStorage.reset() 返回的是 self（同一对象），若直接用它，compile 阶段
        # 的 step() 会推进真实 storage 的计数器；靠"事后 reset 回 -1"能凑效但依赖
        # "compile 总在 step==-1 时调用"这个隐含契约，一旦将来加 resume/retry 就会
        # 踩坑。浅拷贝 + 独立归零 step，让 compile 对真实执行完全无副作用。
        compile_storage = copy.copy(storage)
        if hasattr(compile_storage, "operator_step"):
            compile_storage.operator_step = -1
        pipeline = _ConfigPipeline(compile_storage, ops_and_keys)
        pipeline.compile()
        return {"ok": True, "detail": "compile key check passed", "errors": [], "skipped": False}

    except KeyError as e:
        # DataFlow raises KeyError with a "Key Matching Error ..." message that
        # refers to operators by their internal attr name (_op_0, _op_1, ...).
        # Map those back to the real operator names for a friendly message.
        detail = str(e).strip().strip('"').strip("'")
        for idx, (_operator, _kp, op_name) in enumerate(ops_and_keys):
            detail = detail.replace(f"`_op_{idx}`", f"`{op_name}` (operator #{idx + 1})")
            detail = detail.replace(f"_op_{idx}.run()", f"{op_name}.run()")
        return {
            "ok": False,
            "detail": detail,
            "errors": [{"message": detail}],
            "skipped": False,
        }

    except Exception as e:
        # Any non-KeyError problem (odd run signature, storage read issue, etc.)
        # must NOT block execution — degrade to skip + warn, preserving prior
        # behavior. compile is an added safety net, never a new failure point.
        logger.warning(
            f"[compile] key check skipped due to unexpected error: {e!r}",
            exc_info=True,
        )
        return {
            "ok": True,
            "detail": f"compile check skipped: {e!r}",
            "errors": [],
            "skipped": True,
        }
