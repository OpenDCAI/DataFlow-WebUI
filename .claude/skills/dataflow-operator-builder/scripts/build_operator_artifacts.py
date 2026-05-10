#!/usr/bin/env python3
"""Instantiate DataFlow operator scaffolds from templates."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_TYPES = {"generate", "filter", "refine", "eval"}
VALID_OVERWRITE = {"ask-each", "overwrite-all", "skip-existing"}
VALID_VALIDATION = {"none", "basic", "full"}
IDENTIFIER_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
CLASS_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DataFlow operator artifacts from skill templates")
    parser.add_argument("--spec", required=True, help="Path to JSON spec")
    parser.add_argument("--output-root", required=True, help="Repository root to write generated files")
    parser.add_argument("--skill-dir", default=None, help="Skill directory; default is script parent")
    parser.add_argument(
        "--overwrite",
        choices=sorted(VALID_OVERWRITE),
        default=None,
        help="Override overwrite strategy from spec",
    )
    parser.add_argument(
        "--validation-level",
        choices=sorted(VALID_VALIDATION),
        default=None,
        help="Override validation level from spec",
    )
    parser.add_argument("--log-dir", default=None, help="Optional usage log directory override")
    parser.add_argument("--no-log", action="store_true", help="Disable usage logging")
    parser.add_argument("--dry-run", action="store_true", help="Print file plan without writing")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lstrip("\ufeff").lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"Invalid boolean value for uses_llm: {value!r}")


def _normalize_identifier(raw: Any, field_name: str, pattern: re.Pattern[str]) -> str:
    value = str(raw).strip().replace(".py", "")
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if not pattern.fullmatch(value):
        raise ValueError(f"Invalid {field_name}: {value}")
    return value


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    required = [
        "package_name",
        "operator_type",
        "operator_class_name",
        "operator_module_name",
        "input_key",
        "output_key",
        "uses_llm",
    ]

    missing = [k for k in required if k not in spec or spec[k] is None or str(spec[k]).strip() == ""]
    if missing:
        raise ValueError(f"Missing required spec fields: {missing}")

    operator_type = str(spec["operator_type"]).strip().lower()
    if operator_type not in VALID_TYPES:
        raise ValueError(f"operator_type must be one of {sorted(VALID_TYPES)}, got: {operator_type}")

    package_name = _normalize_identifier(spec["package_name"], "package_name", IDENTIFIER_RE)
    module_name = _normalize_identifier(spec["operator_module_name"], "operator_module_name", IDENTIFIER_RE)
    class_name = _normalize_identifier(spec["operator_class_name"], "operator_class_name", CLASS_NAME_RE)

    input_key = str(spec["input_key"]).strip()
    output_key = str(spec["output_key"]).strip()
    if not input_key:
        raise ValueError("input_key cannot be empty")
    if not output_key:
        raise ValueError("output_key cannot be empty")

    uses_llm = parse_bool(spec["uses_llm"])

    test_prefix_raw = spec.get("test_file_prefix") or module_name
    test_file_prefix = _normalize_identifier(test_prefix_raw, "test_file_prefix", IDENTIFIER_RE)

    cli_module_raw = spec.get("cli_module_name") or f"{module_name}_cli"
    cli_module_name = _normalize_identifier(cli_module_raw, "cli_module_name", IDENTIFIER_RE)

    overwrite_strategy = str(spec.get("overwrite_strategy") or "ask-each").strip().lower()
    if overwrite_strategy not in VALID_OVERWRITE:
        raise ValueError(
            f"overwrite_strategy must be one of {sorted(VALID_OVERWRITE)}, got: {overwrite_strategy}"
        )

    validation_level = str(spec.get("validation_level") or "full").strip().lower()
    if validation_level not in VALID_VALIDATION:
        raise ValueError(
            f"validation_level must be one of {sorted(VALID_VALIDATION)}, got: {validation_level}"
        )

    return {
        "package_name": package_name,
        "operator_type": operator_type,
        "operator_class_name": class_name,
        "operator_module_name": module_name,
        "input_key": input_key,
        "output_key": output_key,
        "uses_llm": uses_llm,
        "cli_module_name": cli_module_name,
        "test_file_prefix": test_file_prefix,
        "overwrite_strategy": overwrite_strategy,
        "validation_level": validation_level,
    }


def render_conditionals(text: str, spec: dict[str, Any]) -> str:
    flags = {
        "USES_LLM": bool(spec["uses_llm"]),
        "NOT_USES_LLM": not bool(spec["uses_llm"]),
        "FILTER": spec["operator_type"] == "filter",
        "NOT_FILTER": spec["operator_type"] != "filter",
    }

    for name, enabled in flags.items():
        pattern = re.compile(rf"\[\[IF_{name}\]\](.*?)\[\[END_IF_{name}\]\]", re.DOTALL)
        text = pattern.sub(lambda m: m.group(1) if enabled else "", text)
    return text


def render_placeholders(text: str, mapping: dict[str, Any]) -> str:
    for key, value in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def read_template(path: Path, spec: dict[str, Any], mapping: dict[str, Any]) -> str:
    text = path.read_text(encoding="utf-8")
    text = render_conditionals(text, spec)
    text = render_placeholders(text, mapping)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    return text


def build_file_plan(skill_dir: Path, output_root: Path, spec: dict[str, Any]) -> list[tuple[Path, Path]]:
    pkg = spec["package_name"]
    operator_type = spec["operator_type"]
    module = spec["operator_module_name"]
    prefix = spec["test_file_prefix"]
    cli_module = spec["cli_module_name"]

    return [
        (
            skill_dir / "assets" / "templates" / "operators" / f"{operator_type}_operator.py.tmpl",
            output_root / pkg / "operators" / operator_type / f"{module}.py",
        ),
        (
            skill_dir / "assets" / "templates" / "cli" / "operator_cli.py.tmpl",
            output_root / pkg / "cli" / f"{cli_module}.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_unit.py.tmpl",
            output_root / "test" / f"test_{prefix}_unit.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_registry.py.tmpl",
            output_root / "test" / f"test_{prefix}_registry.py",
        ),
        (
            skill_dir / "assets" / "templates" / "tests" / "test_operator_smoke.py.tmpl",
            output_root / "test" / f"test_{prefix}_smoke.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "package_init.py.tmpl",
            output_root / pkg / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "operators_root_init.py.tmpl",
            output_root / pkg / "operators" / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "operator_pkg_init.py.tmpl",
            output_root / pkg / "operators" / operator_type / "__init__.py",
        ),
        (
            skill_dir / "assets" / "templates" / "package" / "cli_init.py.tmpl",
            output_root / pkg / "cli" / "__init__.py",
        ),
    ]


def print_plan(plan: list[tuple[Path, Path]], overwrite_mode: str) -> None:
    print("\nPlanned outputs:")
    existing: list[Path] = []
    for _, dest in plan:
        tag = "UPDATE" if dest.exists() else "CREATE"
        print(f"  - [{tag}] {dest}")
        if dest.exists():
            existing.append(dest)

    print(f"\nExisting targets ({len(existing)}):")
    if existing:
        for path in existing:
            print(f"  - {path}")
    else:
        print("  - (none)")

    print(f"\nEffective overwrite strategy: {overwrite_mode}")


def choose_action(dest: Path, overwrite_mode: str) -> str:
    if not dest.exists():
        return "write"
    if overwrite_mode == "overwrite-all":
        return "write"
    if overwrite_mode == "skip-existing":
        return "skip"

    while True:
        answer = input(f"File exists: {dest}\nChoose [o]verwrite / [s]kip / [q]uit: ").strip().lstrip("\ufeff").lower()
        if answer in {"o", "overwrite"}:
            return "write"
        if answer in {"s", "skip"}:
            return "skip"
        if answer in {"q", "quit"}:
            return "quit"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_log_dir(args: argparse.Namespace) -> Path | None:
    if args.no_log:
        return None

    if args.log_dir:
        root = Path(args.log_dir).expanduser().resolve()
    else:
        plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
        if plugin_data:
            root = Path(plugin_data).expanduser() / "dataflow-operator-builder"
        else:
            user_profile = os.environ.get("USERPROFILE")
            base = Path(user_profile).expanduser() if user_profile else Path.home()
            root = base / ".codex_plugin_data" / "dataflow-operator-builder"

    root.mkdir(parents=True, exist_ok=True)
    return root


def log_event(
    log_dir: Path | None,
    event: str,
    spec: dict[str, Any],
    overwrite_mode: str,
    validation_level: str,
    status: str,
    error_message: str | None = None,
) -> None:
    if log_dir is None:
        return

    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "operator_type": spec.get("operator_type"),
        "package_name": spec.get("package_name"),
        "overwrite_mode": overwrite_mode,
        "validation_level": validation_level,
        "status": status,
    }
    if error_message:
        payload["error_message"] = error_message

    log_file = log_dir / "usage.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_files(plan: list[tuple[Path, Path]], spec: dict[str, Any], overwrite_mode: str) -> dict[str, list[Path]]:
    mapping = {
        "PACKAGE_NAME": spec["package_name"],
        "OPERATOR_TYPE": spec["operator_type"],
        "OPERATOR_CLASS_NAME": spec["operator_class_name"],
        "OPERATOR_MODULE": spec["operator_module_name"],
        "INPUT_KEY": spec["input_key"],
        "OUTPUT_KEY": spec["output_key"],
    }

    summary: dict[str, list[Path]] = {"written": [], "skipped": []}
    for template_path, dest in plan:
        action = choose_action(dest, overwrite_mode)
        if action == "quit":
            raise KeyboardInterrupt("User cancelled during overwrite selection")
        if action == "skip":
            summary["skipped"].append(dest)
            continue

        rendered = read_template(template_path, spec=spec, mapping=mapping)
        ensure_parent(dest)
        dest.write_text(rendered, encoding="utf-8")
        summary["written"].append(dest)

    return summary


def expected_test_paths(output_root: Path, test_prefix: str) -> list[Path]:
    return [
        output_root / "test" / f"test_{test_prefix}_unit.py",
        output_root / "test" / f"test_{test_prefix}_registry.py",
        output_root / "test" / f"test_{test_prefix}_smoke.py",
    ]


def _push_sys_path(path: Path) -> bool:
    path_str = str(path)
    if path_str in sys.path:
        return False
    sys.path.insert(0, path_str)
    return True


def _pop_sys_path(path: Path) -> None:
    path_str = str(path)
    while path_str in sys.path:
        sys.path.remove(path_str)


def run_basic_validation(output_root: Path, spec: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    missing_tests = [str(p) for p in expected_test_paths(output_root, spec["test_file_prefix"]) if not p.exists()]
    if missing_tests:
        joined = "\n  - ".join(missing_tests)
        raise RuntimeError(f"Missing generated test files:\n  - {joined}")
    checks.append("Generated test files exist (unit/registry/smoke).")

    module_name = f"{spec['package_name']}.operators.{spec['operator_type']}.{spec['operator_module_name']}"
    class_name = spec["operator_class_name"]

    added = _push_sys_path(output_root)
    try:
        importlib.invalidate_caches()
        module = importlib.import_module(module_name)
        operator_cls = getattr(module, class_name)

        registry_module = importlib.import_module("dataflow.utils.registry")
        registry = getattr(registry_module, "OPERATOR_REGISTRY")

        try:
            in_registry = class_name in registry
        except TypeError:
            in_registry = registry.get(class_name) is not None

        if not in_registry:
            raise RuntimeError(f"Class '{class_name}' is not registered in OPERATOR_REGISTRY")

        resolved_cls = registry.get(class_name)
        if resolved_cls is not operator_cls:
            raise RuntimeError(
                f"OPERATOR_REGISTRY.get('{class_name}') does not resolve to generated class {class_name}"
            )

        checks.append(f"Operator import succeeded: {module_name}.{class_name}.")
        checks.append("Registry resolution check passed.")
    finally:
        if added:
            _pop_sys_path(output_root)

    return checks


class _DummyLLM:
    def __init__(self, operator_type: str):
        self.operator_type = operator_type

    def generate_from_input(self, user_inputs, system_prompt, json_schema=None):
        if self.operator_type == "eval":
            return ["0.80" for _ in user_inputs]
        return [f"mock::{text}" for text in user_inputs]


def _instantiate_operator(operator_cls: type, spec: dict[str, Any]):
    init_signature = inspect.signature(operator_cls.__init__)
    if spec["uses_llm"] and "llm_serving" in init_signature.parameters:
        return operator_cls(llm_serving=_DummyLLM(spec["operator_type"]))
    return operator_cls()


def run_full_validation(output_root: Path, spec: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    module_name = f"{spec['package_name']}.operators.{spec['operator_type']}.{spec['operator_module_name']}"
    class_name = spec["operator_class_name"]

    added = _push_sys_path(output_root)
    try:
        importlib.invalidate_caches()
        module = importlib.import_module(module_name)
        operator_cls = getattr(module, class_name)

        storage_module = importlib.import_module("dataflow.utils.storage")
        file_storage_cls = getattr(storage_module, "FileStorage")

        with tempfile.TemporaryDirectory(prefix="dfop_builder_") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.jsonl"
            input_row = {spec["input_key"]: "hello world"}
            input_path.write_text(json.dumps(input_row, ensure_ascii=False) + "\n", encoding="utf-8")

            storage = file_storage_cls(
                first_entry_file_name=str(input_path),
                cache_path=str(temp_path),
                file_name_prefix="validation_cache",
                cache_type="jsonl",
            )
            operator = _instantiate_operator(operator_cls, spec)

            if spec["operator_type"] == "filter":
                result_key = operator.run(
                    storage=storage.step(),
                    input_key=spec["input_key"],
                    output_key=spec["output_key"],
                    min_length=1,
                    drop_filtered=False,
                )
            else:
                result_key = operator.run(
                    storage=storage.step(),
                    input_key=spec["input_key"],
                    output_key=spec["output_key"],
                )

            if result_key not in {spec["output_key"], None}:
                raise RuntimeError(
                    f"Smoke run returned unexpected key: {result_key!r}; expected {spec['output_key']!r} or None"
                )

            output_file = temp_path / "validation_cache_step1.jsonl"
            if not output_file.exists():
                raise RuntimeError(f"Smoke output file not found: {output_file}")

            raw_lines = [line for line in output_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not raw_lines:
                raise RuntimeError("Smoke output file is empty")

            try:
                first_record = json.loads(raw_lines[0])
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Smoke output first line is not valid JSON: {exc}") from exc

            if spec["output_key"] not in first_record:
                raise RuntimeError(
                    f"Smoke output record does not contain output key '{spec['output_key']}'"
                )

            checks.append("Runtime smoke execution succeeded.")
            checks.append(f"Smoke output contains output key: {spec['output_key']}.")
    finally:
        if added:
            _pop_sys_path(output_root)

    return checks


def run_validation(level: str, output_root: Path, spec: dict[str, Any]) -> list[str]:
    if level == "none":
        return ["Validation skipped (none)."]

    checks = run_basic_validation(output_root=output_root, spec=spec)
    if level == "full":
        checks.extend(run_full_validation(output_root=output_root, spec=spec))
    return checks


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    skill_dir = Path(args.skill_dir).resolve() if args.skill_dir else script_dir.parent
    output_root = Path(args.output_root).resolve()
    log_dir = resolve_log_dir(args)

    spec: dict[str, Any] = {}
    overwrite_mode = "ask-each"
    validation_level = "full"

    try:
        spec = validate_spec(load_json(Path(args.spec).resolve()))
        overwrite_mode = args.overwrite or spec["overwrite_strategy"]
        validation_level = args.validation_level or spec["validation_level"]

        plan = build_file_plan(skill_dir=skill_dir, output_root=output_root, spec=spec)

        print("DataFlow Operator Builder")
        print(f"Skill dir         : {skill_dir}")
        print(f"Output root       : {output_root}")
        print(f"Overwrite         : {overwrite_mode}")
        print(f"Validation level  : {validation_level}")
        print(f"Dry run           : {args.dry_run}")
        print(f"Logging           : {'disabled' if log_dir is None else log_dir}")

        print_plan(plan, overwrite_mode=overwrite_mode)

        if args.dry_run:
            print("\nDry-run complete. No files were written.")
            log_event(
                log_dir,
                event="dry_run",
                spec=spec,
                overwrite_mode=overwrite_mode,
                validation_level=validation_level,
                status="ok",
            )
            return 0

        confirm = input("\nProceed with file generation? [y/N]: ").strip().lstrip("\ufeff").lower()
        if confirm not in {"y", "yes"}:
            print("Cancelled.")
            log_event(
                log_dir,
                event="cancelled",
                spec=spec,
                overwrite_mode=overwrite_mode,
                validation_level=validation_level,
                status="cancelled",
            )
            return 1

        log_event(
            log_dir,
            event="generate_start",
            spec=spec,
            overwrite_mode=overwrite_mode,
            validation_level=validation_level,
            status="started",
        )

        summary = write_files(plan=plan, spec=spec, overwrite_mode=overwrite_mode)

        print("\nGeneration complete.")
        print(f"Written ({len(summary['written'])}):")
        for path in summary["written"]:
            print(f"  - {path}")
        print(f"Skipped ({len(summary['skipped'])}):")
        for path in summary["skipped"]:
            print(f"  - {path}")

        log_event(
            log_dir,
            event="generate_done",
            spec=spec,
            overwrite_mode=overwrite_mode,
            validation_level=validation_level,
            status="ok",
        )

        validation_checks = run_validation(level=validation_level, output_root=output_root, spec=spec)
        print("\nValidation checks:")
        for item in validation_checks:
            print(f"  - [PASS] {item}")

        validate_status = "skipped" if validation_level == "none" else "ok"
        log_event(
            log_dir,
            event="validate_done",
            spec=spec,
            overwrite_mode=overwrite_mode,
            validation_level=validation_level,
            status=validate_status,
        )

        return 0
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        log_event(
            log_dir,
            event="cancelled",
            spec=spec,
            overwrite_mode=overwrite_mode,
            validation_level=validation_level,
            status="cancelled",
            error_message="KeyboardInterrupt",
        )
        return 130
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        log_event(
            log_dir,
            event="error",
            spec=spec,
            overwrite_mode=overwrite_mode,
            validation_level=validation_level,
            status="failed",
            error_message=str(exc),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
