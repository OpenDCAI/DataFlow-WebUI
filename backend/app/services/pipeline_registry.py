import json
import uuid
import datetime
import os
import ast
import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple, Union
from app.core.logger_setup import get_logger
from app.core.config import settings
from app.schemas.pipelines import PipelineValidationIssue, PipelineValidationResult
# from app.services.operator_registry import _op_registry
from app.core.container import container
logger = get_logger(__name__)

from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineFileAnalyzer:
    file_path: str
    source: str
    tree: ast.AST

    @classmethod
    def from_file(cls, file_path: str) -> "PipelineFileAnalyzer":
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        return cls(file_path=file_path, source=source, tree=ast.parse(source))

    def operators(self) -> List[Dict[str, Any]]:
        """返回 [{'name': class_name, 'params': {}}...]"""
        names = self.execution_order()
        return [{"name": n, "params": {}} for n in names]

    def execution_order(self) -> List[str]:
        """按 forward() 中 self.xxx.run() 的出现顺序提取 operator 类名"""
        var_to_class = self._build_var_to_class_map()
        out: List[str] = []

        for class_node in self._iter_class_defs():
            forward = self._find_method(class_node, "forward")
            if not forward:
                continue
            for stmt in forward.body:
                self._collect_run_calls(stmt, var_to_class, out)

        return out

    def init_params_by_class(self) -> Dict[str, Dict[str, Any]]:
        """提取 __init__ 中 self.xxx = OpClass(...keyword args...)"""
        result: Dict[str, Dict[str, Any]] = {}
        for class_node in self._iter_class_defs():
            init = self._find_method(class_node, "__init__")
            if not init:
                continue

            for stmt in init.body:
                class_name, kwargs = self._parse_self_assign_call(stmt)
                if class_name:
                    result[class_name] = kwargs
        return result

    def run_params_by_class(self) -> Dict[str, Dict[str, Any]]:
        """提取 forward 中 self.xxx.run(...keyword args...)"""
        var_to_class = self._build_var_to_class_map()
        result: Dict[str, Dict[str, Any]] = {}

        def visit(node: ast.AST):
            if isinstance(node, ast.Call) and self._is_self_var_run_call(node):
                var_name = node.func.value.attr  # type: ignore[attr-defined]
                class_name = var_to_class.get(var_name)
                if class_name:
                    kwargs = {
                        kw.arg: self._node_to_value(kw.value)
                        for kw in node.keywords
                        if kw.arg is not None
                    }
                    result[class_name] = kwargs

            for child in ast.iter_child_nodes(node):
                visit(child)

        for class_node in self._iter_class_defs():
            forward = self._find_method(class_node, "forward")
            if not forward:
                continue
            for stmt in forward.body:
                visit(stmt)

        return result

    # ---------- Internal helpers ----------

    def _iter_class_defs(self) -> List[ast.ClassDef]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]

    def _find_method(self, class_node: ast.ClassDef, name: str) -> Optional[ast.FunctionDef]:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == name:
                return item
        return None

    def _build_var_to_class_map(self) -> Dict[str, str]:
        """
        从 __init__ 中解析 self.var = Class()，建立 var -> Class 映射
        """
        mapping: Dict[str, str] = {}

        for class_node in self._iter_class_defs():
            init = self._find_method(class_node, "__init__")
            if not init:
                continue

            for stmt in init.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if not self._is_self_attr(target):
                        continue
                    var_name = target.attr  # self.<var_name>
                    if isinstance(stmt.value, ast.Call):
                        class_name = self._call_target_name(stmt.value)
                        if class_name:
                            mapping[var_name] = class_name

        return mapping

    def _collect_run_calls(self, node: ast.AST, var_to_class: Dict[str, str], out: List[str]) -> None:
        """
        递归收集 self.xxx.run() 出现顺序
        """
        if isinstance(node, ast.Call) and self._is_self_var_run_call(node):
            var_name = node.func.value.attr  # type: ignore[attr-defined]
            class_name = var_to_class.get(var_name)
            if class_name:
                out.append(class_name)

        for child in ast.iter_child_nodes(node):
            self._collect_run_calls(child, var_to_class, out)

    def _is_self_var_run_call(self, node: ast.Call) -> bool:
        """
        是否形如：self.xxx.run(...)
        """
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "run"):
            return False
        # node.func.value == self.xxx
        if not isinstance(node.func.value, ast.Attribute):
            return False
        if not (isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "self"):
            return False
        return True

    def _parse_self_assign_call(self, stmt: ast.stmt) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        解析：self.xxx = SomeClass(...kwargs...)
        返回 (SomeClass, kwargs)
        """
        if not isinstance(stmt, ast.Assign):
            return None, {}
        # 仅处理 self.xxx = Call(...)
        if not any(self._is_self_attr(t) for t in stmt.targets):
            return None, {}
        if not isinstance(stmt.value, ast.Call):
            return None, {}

        class_name = self._call_target_name(stmt.value)
        if not class_name:
            return None, {}

        kwargs: Dict[str, Any] = {}
        for kw in stmt.value.keywords:
            if kw.arg is not None:
                kwargs[kw.arg] = self._node_to_value(kw.value)
        return class_name, kwargs

    def _is_self_attr(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        )

    def _call_target_name(self, call: ast.Call) -> Optional[str]:
        """
        获取 Call 的目标名：Class() / module.Class()
        """
        if isinstance(call.func, ast.Name):
            return call.func.id
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        return None

    @staticmethod
    def _node_to_value(node: ast.AST) -> Any:
        """
        把 AST 节点尽量转成 Python 值；不能静态求值的返回 None
        """
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [PipelineFileAnalyzer._node_to_value(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(PipelineFileAnalyzer._node_to_value(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return {
                PipelineFileAnalyzer._node_to_value(k): PipelineFileAnalyzer._node_to_value(v)
                for k, v in zip(node.keys, node.values)
            }
        if isinstance(node, ast.Name):
            return None  # 变量名，静态无法解析
        if isinstance(node, ast.Attribute):
            # self.xxx -> None；其他 attr 返回可读字符串
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                return None
            left = PipelineFileAnalyzer._node_to_value(node.value)
            left = "" if left is None else str(left)
            full = f"{left}.{node.attr}" if left else node.attr
            full = full.replace("<var:", "").replace(">", "")
            return f"<class '{full}'>"
        if isinstance(node, ast.Call):
            # Prompt 类实例化：返回可读类名（沿用你原来的逻辑）
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name and "Prompt" in func_name:
                return f"<class 'dataflow.prompts.{func_name}'>"
            return None

        return None


class PipelineRegistry:
    def __init__(self, path: str | None = None):
        """
        初始化Pipeline注册表i
        加载api_pipelines目录中的所有py文件并提取operator执行顺序
        """
        # using absolute path
        self.path = os.path.join(settings.BASE_DIR, "data", "pipeline_registry.json")

        self._init_registry_file()
        # 初始化后，更新所有api pipeline的operators列表
        self._update_all_api_pipelines_operators()
        
    def _read(self) -> Dict:
        """读取注册表文件"""
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f) or {"pipelines": {}}

    def _write(self, data: Dict):
        """写入注册表文件"""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)    

    def _init_registry_file(self):
        """
        Ensure registry file exists, and load all py files in api_pipelines directory
        """
        logger.info("Initializing Pipeline Registry and Execution Result Table...")

        # only re-init when the registry file does not exist or this json is empty, like { "pipelines": {} }
        need_init_flag = False
        if not os.path.exists(self.path):
            need_init_flag = True
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                    if not content.get("pipelines"):
                        need_init_flag = True
                    elif len(content.get("pipelines")) == 0:
                        need_init_flag = True
                except Exception:
                    need_init_flag = True

        if need_init_flag:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            # 创建初始数据结构
            initial_data = {"pipelines": {}}
            
            # 尝试加载api_pipelines目录中的py文件
            try:
                # 直接使用settings中的路径作为相对路径的开头
                api_pipelines_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
                
                logger.info(f"Checking for API pipelines in: {api_pipelines_dir}")
                
                # 如果目录存在，扫描所有py文件
                if os.path.exists(api_pipelines_dir):
                    logger.info(f"API pipelines directory found, scanning for Python files")
                    
                    # 获取当前时间
                    current_time = self.get_current_time()
                    
                    # 遍历目录中的所有py文件
                    for filename in os.listdir(api_pipelines_dir):
                        if filename.endswith(".py") and not filename.startswith("__"):
                            # 生成pipeline_id
                            pipeline_id = str(uuid.uuid4())
                            file_path = os.path.join(api_pipelines_dir, filename)
                            
                            # 提取operator执行顺序
                            analyzer = PipelineFileAnalyzer.from_file(file_path)
                            operators = analyzer.operators()
                            
                            # 查找关联的数据集
                            input_dataset = self._find_dataset_id(file_path)

                            # 创建pipeline配置
                            pipeline_data = {
                                "id": pipeline_id,
                                "name": filename[:-3].replace("_", " ").title(),
                                "config": {
                                    "file_path": file_path,
                                    "input_dataset": input_dataset,
                                    "operators": operators,
                                },
                                # 从代码目录(api_pipelines)提取的预置 Pipeline
                                "tags": ["api", "template"],
                                "created_at": current_time,
                                "updated_at": current_time,
                                "status": "queued"
                            }
                            
                            # 添加到初始数据中
                            initial_data["pipelines"][pipeline_id] = pipeline_data
                            logger.info(f"Added API pipeline: {pipeline_data['name']} ({pipeline_id}) with {len(operators)} operators")
                    
                    logger.info(f"Successfully loaded {len(initial_data['pipelines'])} API pipelines")
                    
                    # Enrich 所有新建的 pipelines 的参数信息
                    logger.info("Enriching pipeline operators with parameter definitions...")
                    for pipeline_id, pipeline_data in initial_data["pipelines"].items():
                        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                        initial_data["pipelines"][pipeline_id] = enriched_pipeline
                    logger.info("Pipeline operators enrichment completed")
                else:
                    logger.warning(f"API pipelines directory not found: {api_pipelines_dir}")
            except Exception as e:
                logger.error(f"Error loading API pipelines: {e}", exc_info=True)
                # 即使出错，仍然创建基本的注册表文件
            
            # 写入初始数据到文件
            self._write(initial_data)
    
    def _find_dataset_id(self, pipeline_file_path: str) -> Union[str, Dict[str, Any]]:
        """
        从pipeline文件中查找first_entry_file_name，并找到对应的数据集ID
        返回 {"id": "...", "location": [0, 0]} 或 ""
        """
        try:
            if not os.path.exists(pipeline_file_path):
                return ""
                
            with open(pipeline_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找 first_entry_file_name="..."
            match = re.search(r'first_entry_file_name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                relative_path = match.group(1)
                # 解析绝对路径（相对于当前 pipeline 文件所在目录）
                pipeline_dir = os.path.dirname(pipeline_file_path)
                abs_path = os.path.normpath(os.path.join(pipeline_dir, relative_path))

                # 使用 DATAFLOW_CORE_DIR 进行规范化，得到形如：
                #   dataflow_core/example_data/ReasoningPipeline/pipeline_general.json
                # 这样的相对路径（相对于 backend/data/）
                data_parent_dir = os.path.dirname(settings.DATAFLOW_CORE_DIR)  # .../backend/data
                rel_path_from_data_root = os.path.relpath(abs_path, data_parent_dir)
                
                # 尝试从DatasetRegistry中查找
                
                # 1. 尝试通过路径匹配
                all_datasets = container.dataset_registry.list()
                for ds in all_datasets:
                    root = ds.get("root")
                    # 兼容两种存储方式：
                    # 1) 绝对路径（scan_all_datasets 自动注册）
                    # 2) 相对于 backend/data/ 的路径（例如 dataflow_core/example_data/...）
                    if root == abs_path or root == rel_path_from_data_root:
                        return {"id": ds.get("id"), "location": [0, 0]}
                
                # 2. 如果没找到，尝试计算ID查找 (作为备选)，同时兼容绝对路径和相对路径两种情况
                candidate_paths = [abs_path, rel_path_from_data_root]
                for p in candidate_paths:
                    ds_id = hashlib.md5(str(p).encode("utf-8")).hexdigest()[:10]
                    if container.dataset_registry.get(ds_id):
                        return {"id": ds_id, "location": [0, 0]}
                    
        except Exception as e:
            logger.warning(f"Failed to find dataset for pipeline {pipeline_file_path}: {e}")
        
        return ""

    def _update_all_api_pipelines_operators(self):
        """
        更新所有api pipeline的operators列表和input_dataset，
        同时发现并注册 api_pipelines 目录中新增的 .py 文件
        """
        try:
            data = self._read()
            api_pipelines_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
            logger.info(f"Scanning api_pipelines dir: {api_pipelines_dir}")
            if not os.path.exists(api_pipelines_dir):
                logger.warning(f"API pipelines directory not found: {api_pipelines_dir}")
                return
            
            updated = False

            existing_file_paths = set()
            for pipeline_id, pipeline_data in data.get("pipelines", {}).items():
                if "api" in pipeline_data.get("tags", []):
                    fp = pipeline_data.get("config", {}).get("file_path", "")
                    if fp:
                        existing_file_paths.add(os.path.normpath(fp))

            for filename in os.listdir(api_pipelines_dir):
                if not filename.endswith(".py") or filename.startswith("__"):
                    continue
                file_path = os.path.join(api_pipelines_dir, filename)
                if os.path.normpath(file_path) in existing_file_paths:
                    continue
                try:
                    analyzer = PipelineFileAnalyzer.from_file(file_path)
                    operators = analyzer.operators()
                    input_dataset = self._find_dataset_id(file_path)
                    current_time = self.get_current_time()
                    new_id = str(uuid.uuid4())
                    pipeline_entry = {
                        "id": new_id,
                        "name": filename[:-3].replace("_", " ").title(),
                        "config": {
                            "file_path": file_path,
                            "input_dataset": input_dataset,
                            "operators": operators,
                        },
                        "tags": ["api", "template"],
                        "created_at": current_time,
                        "updated_at": current_time,
                        "status": "queued",
                    }
                    enriched = self._enrich_pipeline_operators_internal(pipeline_entry)
                    data["pipelines"][new_id] = enriched
                    updated = True
                    logger.info(f"Discovered new API pipeline: {enriched['name']} ({new_id})")
                except Exception as e:
                    logger.warning(f"Failed to register new pipeline {filename}: {e}")

            # 遍历所有pipeline
            for pipeline_id, pipeline_data in data.get("pipelines", {}).items():
                # 检查是否是api pipeline
                if "api" in pipeline_data.get("tags", []):
                    # 历史数据兼容：确保从代码提取的预置 Pipeline 都带 template tag
                    tags = pipeline_data.get("tags", [])
                    if "template" not in tags:
                        tags.append("template")
                        pipeline_data["tags"] = tags
                        data["pipelines"][pipeline_id] = pipeline_data
                        data["pipelines"][pipeline_id]["updated_at"] = self.get_current_time()
                        updated = True

                    file_path = pipeline_data.get("config", {}).get("file_path")
                    if file_path and os.path.exists(file_path):
                        # 提取operator执行顺序
                        analyzer = PipelineFileAnalyzer.from_file(file_path)
                        operators = analyzer.operators()
                        
                        # 查找关联的数据集
                        input_dataset = self._find_dataset_id(file_path)
                        
                        # 检查是否有变化
                        config_changed = False
                        
                        if pipeline_data["config"].get("operators", []) != operators:
                            pipeline_data["config"]["operators"] = operators
                            config_changed = True
                            
                        if input_dataset and pipeline_data["config"].get("input_dataset") != input_dataset:
                            pipeline_data["config"]["input_dataset"] = input_dataset
                            config_changed = True
                            
                        if config_changed:
                            # Enrich 更新后的 pipeline
                            enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                            data["pipelines"][pipeline_id] = enriched_pipeline
                            data["pipelines"][pipeline_id]["updated_at"] = self.get_current_time()
                            updated = True
                            logger.info(f"Updated and enriched pipeline {pipeline_id}")
            
            # 如果有更新，保存到文件
            if updated:
                self._write(data)
        except Exception as e:
            logger.error(f"Error updating API pipeline operators: {e}", exc_info=True)


    def _normalize_pipeline_name(self, name: str) -> str:
        return re.sub(r"\s+", " ", (name or "")).strip()

    def _is_preset_pipeline(self, pipeline: Dict[str, Any]) -> bool:
        tags = pipeline.get("tags") or []
        if "api" in tags:
            return True

        file_path = (pipeline.get("config") or {}).get("file_path") or ""
        if not file_path:
            return False

        api_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
        try:
            return os.path.commonpath([os.path.abspath(file_path), os.path.abspath(api_dir)]) == os.path.abspath(api_dir)
        except Exception:
            return False

    def _is_visible_pipeline(self, pipeline: Dict[str, Any]) -> bool:
        if self._is_preset_pipeline(pipeline):        
            name = self._normalize_pipeline_name(pipeline.get("name", ""))
            return name in settings._PRESET_PIPELINE_NAME_WHITELIST
        return True

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有预置(template) Pipelines"""
        data = self._read()
        pipelines = list(data.get("pipelines", {}).values())
        templates = [
            p
            for p in pipelines
            if "template" in (p.get("tags") or []) and self._is_visible_pipeline(p)
        ]
        templates.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return templates
    
    def _parse_frontend_params(self, params):
        if not params:
            return {}
        if isinstance(params, dict):
            if "init" in params or "run" in params:
                merged = {}
                for section in ("init", "run"):
                    section_val = params.get(section, []) or []
                    if isinstance(section_val, dict):
                        merged.update(section_val)
                    elif isinstance(section_val, list):
                        for item in section_val:
                            if isinstance(item, dict):
                                name = item.get("name")
                                if name is not None:
                                    merged[name] = item.get("value")
                return merged
            return params
        parsed = {}
        for item in params:
            if isinstance(item, dict):
                key = item.get("name")
                value = item.get("value")
                if key is not None:
                    parsed[key] = value
        return parsed

    def _extract_dataset_id(self, input_dataset: Any) -> Optional[str]:
        if isinstance(input_dataset, dict):
            return input_dataset.get("id")
        if isinstance(input_dataset, str):
            return input_dataset
        return None

    def _make_validation_issue(
        self,
        *,
        level: str,
        code: str,
        message: str,
        operator_index: int | None = None,
        operator_name: str | None = None,
        param_name: str | None = None,
        field_name: str | None = None,
        available_fields: list[str] | None = None,
        suggested_fields: list[str] | None = None,
        repair_hint: str | None = None,
    ) -> PipelineValidationIssue:
        return PipelineValidationIssue(
            level=level,
            code=code,
            message=message,
            operator_index=operator_index,
            operator_name=operator_name,
            param_name=param_name,
            field_name=field_name,
            available_fields=available_fields or [],
            suggested_fields=suggested_fields or [],
            repair_hint=repair_hint,
        )

    def _split_operator_params(
        self,
        op_name: str,
        raw_params: Any,
        op_details: Optional[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        op_details = op_details or container.operator_registry.get_op_details(op_name)
        if not raw_params:
            return {}, {}, op_details

        if isinstance(raw_params, dict) and ("init" in raw_params or "run" in raw_params):
            init_val = raw_params.get("init", []) or []
            run_val = raw_params.get("run", []) or []
            init_parsed = init_val if isinstance(init_val, dict) else self._parse_frontend_params(init_val)
            run_parsed = run_val if isinstance(run_val, dict) else self._parse_frontend_params(run_val)
            return (init_parsed, run_parsed, op_details)

        merged = self._parse_frontend_params(raw_params)
        init_names = {
            item.get("name")
            for item in (op_details or {}).get("parameter", {}).get("init", [])
            if item.get("name")
        }
        run_names = {
            item.get("name")
            for item in (op_details or {}).get("parameter", {}).get("run", [])
            if item.get("name")
        }
        init_params: Dict[str, Any] = {}
        run_params: Dict[str, Any] = {}
        for key, value in merged.items():
            if key in init_names and key not in run_names:
                init_params[key] = value
            else:
                run_params[key] = value
        return init_params, run_params, op_details

    @staticmethod
    def _looks_like_input_field_param(param_name: str) -> bool:
        if param_name.startswith("output_") or param_name.endswith("_output_key"):
            return False
        return (
            param_name.startswith("input_")
            or param_name.endswith("_input_key")
            or (param_name.endswith("_key") and param_name != "output_key")
            or param_name.endswith("_keys")
        )

    @staticmethod
    def _looks_like_output_field_param(param_name: str) -> bool:
        return param_name.startswith("output_") or param_name == "output_key" or param_name.endswith("_output_key")

    @staticmethod
    def _extract_serving_id(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            serving_id = value.get("id") or value.get("serving_id")
            return str(serving_id) if serving_id else None
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _suggest_similar_fields(field_name: str, available_fields: List[str], limit: int = 3) -> List[str]:
        if not field_name or not available_fields:
            return []

        import difflib

        normalized_map: Dict[str, str] = {}
        for candidate in available_fields:
            normalized = re.sub(r"[^a-z0-9]+", "", str(candidate).lower())
            if normalized and normalized not in normalized_map:
                normalized_map[normalized] = candidate

        normalized_field = re.sub(r"[^a-z0-9]+", "", str(field_name).lower())
        suggestions: List[str] = []
        if normalized_field and normalized_map:
            normalized_matches = difflib.get_close_matches(
                normalized_field,
                list(normalized_map.keys()),
                n=limit,
                cutoff=0.45,
            )
            for match in normalized_matches:
                candidate = normalized_map[match]
                if candidate not in suggestions:
                    suggestions.append(candidate)

        direct_matches = difflib.get_close_matches(
            str(field_name),
            [str(item) for item in available_fields],
            n=limit,
            cutoff=0.45,
        )
        for match in direct_matches:
            if match not in suggestions:
                suggestions.append(match)

        return suggestions[:limit]

    @classmethod
    def _build_missing_input_field_hint(
        cls,
        *,
        field_name: str,
        param_name: str,
        available_fields: List[str],
    ) -> tuple[List[str], str]:
        suggestions = cls._suggest_similar_fields(field_name, available_fields)
        if suggestions:
            hint = (
                f"将参数 '{param_name}' 从 '{field_name}' 改成最接近的真实字段之一："
                + ", ".join(suggestions)
                + "；若这些都不对，就先查看 get_dataset_columns / 上游 output_key 再修正。"
            )
        else:
            hint = (
                f"字段 '{field_name}' 当前不存在。先用 get_dataset_columns 确认输入列名，"
                f"再检查上游 output_key 是否真的产出了 '{field_name}'。"
            )
        return suggestions, hint

    def _collect_input_field_refs(
        self,
        run_params: Dict[str, Any],
        run_defs: List[Dict[str, Any]],
    ) -> List[Tuple[str, str]]:
        refs: List[Tuple[str, str]] = []
        fixed_run_names = {item.get("name") for item in run_defs if item.get("name")}
        has_var_kwargs = any(item.get("kind") == "VAR_KEYWORD" for item in run_defs)

        for param_name, value in run_params.items():
            if value is None:
                continue

            if self._looks_like_input_field_param(param_name):
                if isinstance(value, str):
                    refs.append((param_name, value))
                elif isinstance(value, list):
                    refs.extend((param_name, item) for item in value if isinstance(item, str))
                elif isinstance(value, dict):
                    refs.extend((param_name, item) for item in value.values() if isinstance(item, str))
                continue

            if has_var_kwargs and param_name not in fixed_run_names and isinstance(value, str):
                refs.append((param_name, value))

        return refs

    def _collect_output_field_refs(self, run_params: Dict[str, Any]) -> List[Tuple[str, str]]:
        refs: List[Tuple[str, str]] = []
        for param_name, value in run_params.items():
            if value is None or not self._looks_like_output_field_param(param_name):
                continue
            if isinstance(value, str):
                refs.append((param_name, value))
            elif isinstance(value, list):
                refs.extend((param_name, item) for item in value if isinstance(item, str))
        return refs

    @staticmethod
    def _maybe_parse_json_container(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped or stripped[0] not in "[{":
            return value
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value

    @classmethod
    def _normalize_dynamic_code_param(cls, value: Any, *, param_name: str) -> Tuple[Optional[List[Any]], Optional[str]]:
        value = cls._maybe_parse_json_container(value)

        if callable(value):
            return [value], None

        if isinstance(value, str):
            code = value.strip()
            if code.startswith("lambda ") or code.startswith("def "):
                return [code], None
            return None, (
                f"参数 '{param_name}' 必须是 lambda/def 代码字符串、包含 code 字段的对象，"
                "或这两种形式组成的列表。"
            )

        if isinstance(value, dict):
            code = value.get("code")
            if isinstance(code, str) and code.strip():
                return cls._normalize_dynamic_code_param(code, param_name=param_name)
            return None, f"参数 '{param_name}' 的对象形式缺少非空 code 字段。"

        if isinstance(value, list):
            normalized: List[Any] = []
            for item in value:
                child_items, child_error = cls._normalize_dynamic_code_param(item, param_name=param_name)
                if child_error:
                    return None, child_error
                normalized.extend(child_items or [])
            if not normalized:
                return None, f"参数 '{param_name}' 至少需要包含一条可执行规则。"
            return normalized, None

        return None, (
            f"参数 '{param_name}' 的类型不受支持：{type(value).__name__}。"
            "请传代码字符串、对象或列表。"
        )

    def validate_pipeline_config(self, config: Dict[str, Any]) -> PipelineValidationResult:
        errors: List[PipelineValidationIssue] = []
        warnings: List[PipelineValidationIssue] = []

        dataset_id = self._extract_dataset_id(config.get("input_dataset"))
        available_fields: List[str] = []

        if not dataset_id:
            errors.append(self._make_validation_issue(
                level="error",
                code="missing_input_dataset",
                message="Pipeline config 缺少 input_dataset.id，后端无法解析输入数据集。",
            ))
        else:
            dataset = container.dataset_registry.get(dataset_id)
            if not dataset:
                errors.append(self._make_validation_issue(
                    level="error",
                    code="dataset_not_found",
                    message=f"输入数据集 '{dataset_id}' 未注册，create/update 后执行会直接失败。",
                    field_name=dataset_id,
                ))
            else:
                try:
                    available_fields = list(container.dataset_registry.get_columns(dataset_id) or [])
                except Exception as exc:
                    logger.warning(f"Failed to inspect dataset columns for {dataset_id}: {exc}")
                    available_fields = []
                if not available_fields:
                    warnings.append(self._make_validation_issue(
                        level="warning",
                        code="dataset_columns_unavailable",
                        message=(
                            f"数据集 '{dataset_id}' 的列名不可用，后端无法提前校验字段流。"
                            " 如果这是 json/jsonl/parquet 以外的格式，建议先转成可枚举列名的数据集。"
                        ),
                        field_name=dataset_id,
                    ))

        current_fields = list(available_fields)
        operators = config.get("operators", []) or []

        for idx, op in enumerate(operators):
            op_name = op.get("name") or f"operator_{idx}"
            init_params, run_params, op_details = self._split_operator_params(op_name, op.get("params"))

            if not op_details:
                errors.append(self._make_validation_issue(
                    level="error",
                    code="unknown_operator",
                    message=f"算子 '{op_name}' 未在 operator registry 中注册。",
                    operator_index=idx,
                    operator_name=op_name,
                    available_fields=current_fields,
                ))
                continue

            if "prompt_template" in init_params and isinstance(init_params.get("prompt_template"), dict):
                prompt_template = init_params.get("prompt_template") or {}
                if not prompt_template.get("cls_name"):
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="invalid_prompt_template_dict",
                        message=(
                            f"算子 '{op_name}' 的 prompt_template 使用了 dict，但缺少 cls_name。"
                            " 仅允许结构化 prompt 对象（含 cls_name）或 prompt 类名字符串。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="prompt_template",
                        available_fields=current_fields,
                    ))

            init_defs = (op_details.get("parameter") or {}).get("init", [])
            init_def_names = {item.get("name") for item in init_defs if item.get("name")}

            for dynamic_param_name in ("process_fn", "filter_rules"):
                if dynamic_param_name not in init_def_names:
                    continue
                dynamic_value = init_params.get(dynamic_param_name)
                if dynamic_value is None:
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="missing_dynamic_code_param",
                        message=f"算子 '{op_name}' 缺少必需参数 '{dynamic_param_name}'。",
                        operator_index=idx,
                        operator_name=op_name,
                        param_name=dynamic_param_name,
                        available_fields=current_fields,
                    ))
                    continue
                _, dynamic_error = self._normalize_dynamic_code_param(
                    dynamic_value,
                    param_name=dynamic_param_name,
                )
                if dynamic_error:
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="invalid_dynamic_code_param",
                        message=f"算子 '{op_name}' 的参数 '{dynamic_param_name}' 非法：{dynamic_error}",
                        operator_index=idx,
                        operator_name=op_name,
                        param_name=dynamic_param_name,
                        available_fields=current_fields,
                    ))

            if "llm_serving" in init_def_names:
                raw_serving = init_params.get("llm_serving")
                serving_id = self._extract_serving_id(raw_serving)
                if raw_serving is None:
                    warnings.append(self._make_validation_issue(
                        level="warning",
                        code="missing_llm_serving",
                        message=(
                            f"算子 '{op_name}' 依赖 llm_serving，但当前配置未显式指定。"
                            " 运行时可能依赖默认 serving 自动填充，稳定性和可解释性都会变差。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="llm_serving",
                        available_fields=current_fields,
                    ))
                elif not serving_id:
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="invalid_serving_reference",
                        message=(
                            f"算子 '{op_name}' 的 llm_serving 不是可解析的 serving id。"
                            " 请输入真实的 serving id，或传入带 `id` / `serving_id` 的对象。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="llm_serving",
                        available_fields=current_fields,
                    ))
                elif not container.serving_registry or not container.serving_registry._get(serving_id):
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="serving_not_found",
                        message=f"算子 '{op_name}' 引用了不存在的 llm_serving '{serving_id}'。",
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="llm_serving",
                        field_name=serving_id,
                        available_fields=current_fields,
                    ))

            if "embedding_serving" in init_def_names:
                raw_embedding_serving = init_params.get("embedding_serving")
                embedding_serving_id = self._extract_serving_id(raw_embedding_serving)
                if raw_embedding_serving is not None and not embedding_serving_id:
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="invalid_serving_reference",
                        message=(
                            f"算子 '{op_name}' 的 embedding_serving 不是可解析的 serving id。"
                            " 请输入真实的 serving id，或传入带 `id` / `serving_id` 的对象。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="embedding_serving",
                        available_fields=current_fields,
                    ))
                elif embedding_serving_id and (not container.serving_registry or not container.serving_registry._get(embedding_serving_id)):
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="serving_not_found",
                        message=f"算子 '{op_name}' 引用了不存在的 embedding_serving '{embedding_serving_id}'。",
                        operator_index=idx,
                        operator_name=op_name,
                        param_name="embedding_serving",
                        field_name=embedding_serving_id,
                        available_fields=current_fields,
                    ))

            if "prompt_template" in init_def_names and init_params.get("prompt_template") is not None:
                prompt_template_value = init_params.get("prompt_template")
                allowed_prompts = set(op_details.get("allowed_prompts") or [])
                if isinstance(prompt_template_value, str):
                    if allowed_prompts and prompt_template_value not in allowed_prompts:
                        errors.append(self._make_validation_issue(
                            level="error",
                            code="invalid_prompt_template_class",
                            message=(
                                f"算子 '{op_name}' 的 prompt_template='{prompt_template_value}' 不在允许列表中："
                                f"{sorted(allowed_prompts)}。"
                            ),
                            operator_index=idx,
                            operator_name=op_name,
                            param_name="prompt_template",
                            available_fields=current_fields,
                        ))
                elif isinstance(prompt_template_value, dict):
                    cls_name = prompt_template_value.get("cls_name")
                    if cls_name and allowed_prompts and cls_name not in allowed_prompts:
                        errors.append(self._make_validation_issue(
                            level="error",
                            code="invalid_prompt_template_class",
                            message=(
                                f"算子 '{op_name}' 的 prompt_template.cls_name='{cls_name}' 不在允许列表中："
                                f"{sorted(allowed_prompts)}。"
                            ),
                            operator_index=idx,
                            operator_name=op_name,
                            param_name="prompt_template",
                            available_fields=current_fields,
                        ))

            run_defs = (op_details.get("parameter") or {}).get("run", [])
            # 提前拦截「run 里塞了算子 run() 签名之外的参数」这类错误。执行时
            # operator.run(**run_params) 会因未知关键字参数直接崩溃，且真实异常
            # 常被吞掉，所以在 validate 阶段就报 error，让 agent 能立即纠正。
            # 常见误用：把 serving_name / system_prompt / user_prompt（其实属于
            # init）塞进了 run。若算子 run() 声明了 **kwargs（VAR_KEYWORD）则放行。
            run_def_names = {item.get("name") for item in run_defs if item.get("name")}
            run_accepts_kwargs = any(
                item.get("kind") == "VAR_KEYWORD" for item in run_defs
            )
            if run_def_names and not run_accepts_kwargs:
                init_def_name_set = {item.get("name") for item in init_defs if item.get("name")}
                for provided_name in run_params.keys():
                    if provided_name in ("storage",):
                        continue
                    if provided_name not in run_def_names:
                        belongs_to_init = provided_name in init_def_name_set
                        hint = (
                            f" 该参数其实属于该算子的 init 参数，请移到 init。"
                            if belongs_to_init else
                            f" 该算子 run() 只接受：{sorted(run_def_names)}。"
                        )
                        errors.append(self._make_validation_issue(
                            level="error",
                            code="unknown_run_param",
                            message=(
                                f"算子 '{op_name}' 的 run 参数 '{provided_name}' 不在 run() 签名中。"
                                f"{hint}"
                            ),
                            operator_index=idx,
                            operator_name=op_name,
                            param_name=provided_name,
                            available_fields=current_fields,
                        ))

            for param_name, field_name in self._collect_input_field_refs(run_params, run_defs):
                if current_fields and field_name not in current_fields:
                    suggested_fields, repair_hint = self._build_missing_input_field_hint(
                        field_name=field_name,
                        param_name=param_name,
                        available_fields=current_fields,
                    )
                    errors.append(self._make_validation_issue(
                        level="error",
                        code="missing_input_field",
                        message=(
                            f"算子 '{op_name}' 的参数 '{param_name}' 引用了字段 '{field_name}'，"
                            "但它既不在输入数据集中，也不是上游算子已产出的字段。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name=param_name,
                        field_name=field_name,
                        available_fields=current_fields,
                        suggested_fields=suggested_fields,
                        repair_hint=repair_hint,
                    ))

            for param_name, field_name in self._collect_output_field_refs(run_params):
                if field_name in current_fields:
                    warnings.append(self._make_validation_issue(
                        level="warning",
                        code="output_field_overwrite",
                        message=(
                            f"算子 '{op_name}' 的参数 '{param_name}' 将写回已存在字段 '{field_name}'。"
                            " 这会覆盖原始列或上游结果，容易让字段流失真。"
                        ),
                        operator_index=idx,
                        operator_name=op_name,
                        param_name=param_name,
                        field_name=field_name,
                        available_fields=current_fields,
                    ))
                if field_name not in current_fields:
                    current_fields.append(field_name)

        return PipelineValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            dataset_id=dataset_id,
            available_input_fields=available_fields,
            final_available_fields=current_fields,
        )

    def get_current_time(self):
        """获取当前时间的ISO格式字符串"""
        return datetime.datetime.now().isoformat()
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """
        列出所有注册的Pipeline
        在返回之前，确保api pipeline的operators列表是最新的
        """
        # 先更新所有api pipeline的operators列表（会自动 enrich）
        
        data = self._read()
        pipelines = list(data.get("pipelines", {}).values())
        pipelines = [p for p in pipelines if self._is_visible_pipeline(p)]
        
        # 按更新时间倒序排序
        pipelines.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # 直接返回，因为 pipelines 已经在初始化/更新时 enriched
        return pipelines
    
    def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建一个新的Pipeline"""
        data = self._read()
        
        # 生成唯一ID
        pipeline_id = str(uuid.uuid4())
        current_time = self.get_current_time()
        
        # 直接创建字典表示的pipeline
        config = pipeline_data.get("config", {})
        validation = self.validate_pipeline_config(config)
        if not validation.valid:
            joined_errors = "; ".join(issue.message for issue in validation.errors)
            raise ValueError(f"Invalid pipeline configuration: {joined_errors}")
        operators = config.get("operators", [])
        for op in operators:
            params = op.get("params", {})
            op["params"] = self._parse_frontend_params(params)
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name", ""),
            "config": config,
            "tags": pipeline_data.get("tags", []),
            "created_at": current_time,
            "updated_at": current_time,
            "status": "queued"
        }
        
        # Enrich pipeline operators
        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline)
        
        # 保存 enriched pipeline 到文件
        data["pipelines"][pipeline_id] = enriched_pipeline
        self._write(data)
        
        logger.info(f"Successfully created pipeline: {pipeline_id} with name: {pipeline_data.get('name', '')}")
        return enriched_pipeline
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取Pipeline
        如果是api pipeline，确保返回最新的operators列表
        """
        data = self._read()
        pipeline_data = data.get("pipelines", {}).get(pipeline_id)

        if pipeline_data and not self._is_visible_pipeline(pipeline_data):
            return None
        
        if pipeline_data:
            # 如果是api pipeline，检查并更新operators列表
            if "api" in pipeline_data.get("tags", []):
                file_path = pipeline_data.get("config", {}).get("file_path")
                if file_path and os.path.exists(file_path):
                    analyzer = PipelineFileAnalyzer.from_file(file_path)
                    operators = analyzer.operators()
                    existing_op_names = [op.get("name") for op in pipeline_data["config"].get("operators", [])]
                    new_op_names = [op.get("name") for op in operators]
                    
                    # 只有当 operator 列表真正改变时才更新和 enrich
                    if existing_op_names != new_op_names:
                        pipeline_data["config"]["operators"] = operators
                        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                        enriched_pipeline["updated_at"] = self.get_current_time()
                        # 保存更新
                        data["pipelines"][pipeline_id] = enriched_pipeline
                        self._write(data)
                        logger.info(f"Updated and enriched pipeline {pipeline_id} on get")
                        return enriched_pipeline
            
            # 直接返回已 enriched 的数据
            return pipeline_data
        return None
    
    def _update_pipeline_op_info(self, new_op_info: Dict[str, Any], old_op_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        new_op_info: 新的算子信息（字典格式）
        new_op_info 中包含 name, params, location 三个字段
            - single_param_format: {'name': xxx, 'value': yyy}
        old_op_info: 旧的算子信息（字典格式），我们假设其中的所有参数是全的。
        return: 更新后的算子信息（字典格式）
        """
        # if name will be updated, raise an error.
        new_name = new_op_info.get("name")
        old_name = old_op_info.get("name")
        if new_name != old_name:
            raise ValueError(f"Operator name cannot be updated. Original name: {old_name}, New name: {new_name}")
        
        # Update the locations
        if "location" in new_op_info:
            old_op_info["location"] = new_op_info.get("location")
        
        # Parse new params
        new_params = new_op_info.get("params", {})
        new_init_params = self._parse_frontend_params(new_params.get("init", []))
        new_run_params = self._parse_frontend_params(new_params.get("run", []))
        
        # Update Init Params
        old_params = old_op_info.get("params", {})
        for param in old_params.get("init", []):
            param_name = param.get("name")
            if param_name is not None:
                param_value = new_init_params.get(param_name, None)
                if param_value is not None:
                    param["value"] = param_value
                elif param.get('value') is None:
                    param["value"] = param.get("default_value", None)
        
        # Update Run Params
        for param in old_params.get("run", []):
            param_name = param.get("name")
            if param_name is not None:
                param_value = new_run_params.get(param_name, None)
                if param_value is not None:
                    param["value"] = param_value
                elif param.get('value') is None:
                    param["value"] = param.get("default_value", None)
                    
        old_run_params_name_list = [param.get("name") for param in old_params.get("run", [])]
        for param_name, param_value in new_run_params.items():
            if param_name is not None and param_name not in old_run_params_name_list:
                old_params.get("run", []).append({"name": param_name, "value": param_value})
            
        return old_op_info
        
    
    def update_pipeline(self, pipeline_id: str, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新指定的Pipeline"""
        data = self._read()
        
        if pipeline_id not in data.get("pipelines", {}):
            raise ValueError(f"Pipeline with id {pipeline_id} not found")
        
        # 获取当前Pipeline数据并直接更新
        updated_pipeline = data["pipelines"][pipeline_id].copy()
        
        # update Operators
        new_pipeline_config = pipeline_data.get("config", None)
        if new_pipeline_config is not None:
            if "input_dataset" in new_pipeline_config:
                updated_pipeline["config"]["input_dataset"] = new_pipeline_config.get("input_dataset", "")
            if "operators" in new_pipeline_config:
                op_map = {}
                for idx, op in enumerate(updated_pipeline["config"]["operators"]):
                    op_map[f"{op.get('name')}_{idx}"] = op
                
                updated_operators = []
                for idx, op in enumerate(new_pipeline_config["operators"]):
                    old_op_info = op_map.get(f"{op.get('name')}_{idx}", None)
                    if old_op_info is None:  # new operator
                        # 创建新 operator 的字典格式
                        op_details = container.operator_registry.get_op_details(op.get("name"))
                        old_op_info = {
                            "name": op.get("name"),
                            "params": op_details.get("parameter", {"init": [], "run": []}) if op_details else {"init": [], "run": []},
                            "location": op.get("location", (0, 0))
                        }
                    
                    # 更新 operator 信息
                    updated_op = self._update_pipeline_op_info(op, old_op_info)
                    updated_operators.append(updated_op)
                
                # 更新 operators 列表
                updated_pipeline["config"]["operators"] = updated_operators

            validation = self.validate_pipeline_config(updated_pipeline["config"])
            if not validation.valid:
                joined_errors = "; ".join(issue.message for issue in validation.errors)
                raise ValueError(f"Invalid pipeline configuration: {joined_errors}")
            
        
        # 更新字段，保留创建时间和状态
        updated_pipeline.update({
            "name": pipeline_data.get("name", updated_pipeline.get("name", "")),
            # "config": pipeline_data.get("config", updated_pipeline.get("config", {})),
            "tags": pipeline_data.get("tags", updated_pipeline.get("tags", [])),
            "updated_at": self.get_current_time()
            # 保持created_at和status不变
        })
        
        # Enrich pipeline operators
        # enriched_pipeline = self._enrich_pipeline_operators_internal(updated_pipeline)
        
        # 保存 enriched pipeline 到文件
        data["pipelines"][pipeline_id] = updated_pipeline
        self._write(data)
        
        logger.info(f"Updated pipeline: {pipeline_id}")
        return updated_pipeline
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除指定的Pipeline"""
        data = self._read()
        
        if pipeline_id not in data.get("pipelines", {}):
            return False
        
        # 直接从文件删除
        del data["pipelines"][pipeline_id]
        self._write(data)
        
        logger.info(f"Deleted pipeline: {pipeline_id}")
        return True
        

    def _enrich_pipeline_operators_internal(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich pipeline operators with detailed parameter info from registry.
        This method only enriches the data and returns it without saving.
        Also extracts actual parameter values from the pipeline Python file.
        """
        # Deep copy to avoid modifying original data
        pipeline = json.loads(json.dumps(pipeline_data))
        config = pipeline.get("config", {})
        operators = config.get("operators", [])
        
        # 从 pipeline 文件中提取实际参数值（init 和 run）
        file_path = config.get("file_path")
        pipeline_init_params = {}
        pipeline_run_params = {}
        if file_path and os.path.exists(file_path):
            analyzer = PipelineFileAnalyzer.from_file(file_path)
            pipeline_init_params = analyzer.init_params_by_class()
            pipeline_run_params = analyzer.run_params_by_class()
            logger.info(f"Extracted init params for {len(pipeline_init_params)} operators, run params for {len(pipeline_run_params)} operators")
        
        enriched_operators = []
        for op in operators:
            op_copy = op.copy()
            op_name = op.get("name")
            stored_params = op.get("params", {})
            if not isinstance(stored_params, dict):
                stored_params = {}
            
            # 检查是否已经是 enriched 格式（包含 init 和 run 键）
            if "init" in stored_params and "run" in stored_params:
                # 已经是 enriched 格式，直接使用
                enriched_operators.append(op_copy)
                continue
            
            op_details = container.operator_registry.get_op_details(op_name)
            
            # 获取该 operator 在 pipeline 代码中的实际参数值
            actual_init_params = pipeline_init_params.get(op_name, {})
            actual_run_params = pipeline_run_params.get(op_name, {})
            
            enriched_params = {
                "init": [],
                "run": []
            }
            
            if op_details:
                # Process init parameters
                init_defs = op_details.get("parameter", {}).get("init", [])
                processed_init_names = set()
                
                for param_def in init_defs:
                    p_name = param_def.get("name")
                    if not p_name:
                        continue
                    processed_init_names.add(p_name)
                    
                    # Priority: 
                    # 1. actual value from pipeline code (__init__)
                    # 2. stored params (user customized)
                    # 3. default value from operator definition
                    p_val = actual_init_params.get(p_name)
                    if p_val is None:
                        p_val = stored_params.get(p_name)
                    if p_val is None:
                        p_val = param_def.get("default_value")
                    if p_val is None and param_def.get("name") == "prompt_template":
                        # Get @prompt_restrict decorator from operator class
                        if op_details.get("allowed_prompts"):
                            p_val = op_details["allowed_prompts"][0]
                    # Create enriched param object
                    enriched_param = param_def.copy()
                    enriched_param["value"] = p_val
                    enriched_params["init"].append(enriched_param)

                # Process run parameters
                run_defs = op_details.get("parameter", {}).get("run", [])
                processed_run_names = set()
                
                for param_def in run_defs:
                    p_name = param_def.get("name")
                    if not p_name:
                        continue
                    processed_run_names.add(p_name)
                    
                    # Priority:
                    # 1. actual value from pipeline code (forward method's .run() call)
                    # 2. stored params (user customized)
                    # 3. default value from operator definition
                    p_val = actual_run_params.get(p_name)
                    if p_val is None:
                        p_val = stored_params.get(p_name)
                    if p_val is None:
                        p_val = param_def.get("default_value")
                        
                    # Create enriched param object
                    enriched_param = param_def.copy()
                    enriched_param["value"] = p_val
                    enriched_params["run"].append(enriched_param)
                
                # Add any stored params that were not in definition (dynamic params)
                # We put them in 'run' by default as they are likely runtime params
                for k, v in stored_params.items():
                    if k not in processed_init_names and k not in processed_run_names:
                        enriched_params["run"].append({
                            "name": k,
                            "value": v,
                            "default_value": None,
                            "kind": "DYNAMIC",
                            "description": "Dynamic parameter"
                        })
            else:
                # Operator not found in registry, just return stored params in 'run'
                for k, v in stored_params.items():
                    enriched_params["run"].append({
                        "name": k,
                        "value": v
                    })
            
            op_copy["params"] = enriched_params
            enriched_operators.append(op_copy)
            
        pipeline["config"]["operators"] = enriched_operators
        return pipeline
