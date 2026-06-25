"""
UserPromptRegistry：用户自定义 Prompt 模板的本地持久化管理。

与 dataflow.utils.registry.PROMPT_REGISTRY 完全解耦——后者是 DataFlow 内置
prompt 类的反射入口，本 Registry 仅服务"用户在 WebUI 上写的 f-string 模板"。

持久化文件：backend/<RESOURCE_DIR>/prompts/user_templates.json，结构：
  {
    "tpl_xxxxxxx": {
      "id": "tpl_xxxxxxx",
      "name": "...",
      "description": "...",
      "template": "Given {question}, produce ...",
      "allowed_operators": ["OperatorA"],
      "example_variables": { "question": "..." },
      "created_at": "...", "updated_at": "..."
    },
    ...
  }

运行时解引用：算子参数中出现 "user_prompt:<id>" 字符串时，由
param_coercion.resolve_user_prompt_ref(...) 拿到对应模板文本。
"""
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger as log
from app.core.config import settings


BACKEND_DIR = Path(__file__).parent.parent.parent
PROMPTS_DIR = BACKEND_DIR / settings.RESOURCE_DIR / "prompts"
PROMPTS_FILE = PROMPTS_DIR / "user_templates.json"

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _extract_placeholders(template: str) -> List[str]:
    if not template:
        return []
    seen: List[str] = []
    for m in _PLACEHOLDER_RE.finditer(template):
        name = m.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def render_template(template: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Render an f-string template with the given variables. Missing keys are
    reported separately instead of raising, so the UI can flag them inline."""
    placeholders = _extract_placeholders(template)
    missing = [p for p in placeholders if p not in variables]
    if missing:
        safe_vars = {p: "{" + p + "}" for p in placeholders}
        safe_vars.update({k: v for k, v in variables.items() if k in placeholders})
        rendered = template.format(**safe_vars)
    else:
        try:
            rendered = template.format(**{p: variables[p] for p in placeholders})
        except Exception as e:
            rendered = f"[render error: {e}]"
    return {
        "rendered": rendered,
        "placeholders": placeholders,
        "missing": missing,
    }


class UserPromptRegistry:
    """CRUD + template rendering for user-defined prompt templates."""

    def __init__(self):
        self._ensure_storage()
        self._templates: Dict[str, Dict[str, Any]] = self._load()

    # ── storage ──────────────────────────────────────────────
    def _ensure_storage(self):
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        if not PROMPTS_FILE.exists():
            PROMPTS_FILE.write_text("{}")

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            content = PROMPTS_FILE.read_text()
            return json.loads(content) if content.strip() else {}
        except Exception as e:
            log.warning(f"Failed to load user prompt templates: {e}")
            return {}

    def _save(self):
        try:
            PROMPTS_FILE.write_text(
                json.dumps(self._templates, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            log.error(f"Failed to save user prompt templates: {e}")
            raise

    # ── CRUD ─────────────────────────────────────────────────
    def create(
        self,
        name: str,
        description: str,
        template: str,
        allowed_operators: Optional[List[str]] = None,
        example_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tpl_id = f"tpl_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        rec = {
            "id": tpl_id,
            "name": name,
            "description": description or "",
            "template": template or "",
            "allowed_operators": list(allowed_operators or []),
            "example_variables": dict(example_variables or {}),
            "created_at": now,
            "updated_at": now,
        }
        self._templates[tpl_id] = rec
        self._save()
        log.info(f"Created user prompt template {tpl_id}")
        return rec

    def get(self, tpl_id: str) -> Optional[Dict[str, Any]]:
        return self._templates.get(tpl_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._templates.values())

    def update(self, tpl_id: str, **fields) -> Optional[Dict[str, Any]]:
        rec = self._templates.get(tpl_id)
        if not rec:
            return None
        for k in ("name", "description", "template"):
            if fields.get(k) is not None:
                rec[k] = fields[k]
        if fields.get("allowed_operators") is not None:
            rec["allowed_operators"] = list(fields["allowed_operators"])
        if fields.get("example_variables") is not None:
            rec["example_variables"] = dict(fields["example_variables"])
        rec["updated_at"] = datetime.utcnow().isoformat()
        self._save()
        return rec

    def delete(self, tpl_id: str) -> bool:
        if tpl_id in self._templates:
            del self._templates[tpl_id]
            self._save()
            return True
        return False

    # ── helpers ──────────────────────────────────────────────
    def preview(self, template: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        return render_template(template, variables)

    def get_template_text(self, tpl_id: str) -> Optional[str]:
        rec = self._templates.get(tpl_id)
        return rec.get("template") if rec else None
