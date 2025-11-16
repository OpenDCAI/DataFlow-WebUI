"""
算子工具服务层
提供算子库管理、源码获取、RAG检索等功能
从 DataFlow-Agent 的 op_tools.py 迁移而来
"""
import inspect
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

import numpy as np
import faiss
import httpx

from dataflow.utils.registry import OPERATOR_REGISTRY
from app.core.config import settings


class OperatorToolsService:
    """算子工具服务类"""
    
    def __init__(self):
        self.resource_dir = Path(settings.DATA_DIR) / "operator_resources"
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        self.ops_json_path = self.resource_dir / "ops.json"
        
        # 初始化 OPERATOR_REGISTRY
        if hasattr(OPERATOR_REGISTRY, "_init_loaders"):
            OPERATOR_REGISTRY._init_loaders()
        if hasattr(OPERATOR_REGISTRY, "_get_all"):
            OPERATOR_REGISTRY._get_all()
    
    # ============ 算子库管理部分 ============
    
    @staticmethod
    def _safe_json_val(val: Any) -> Any:
        """
        把任意 Python 对象转换成 JSON 可序列化的值
        """
        if val is inspect.Parameter.empty:
            return None
        
        if isinstance(val, (str, int, float, bool)) or val is None:
            return val
        
        if isinstance(val, type):
            return f"{val.__module__}.{val.__qualname__}"
        
        if getattr(val, "__origin__", None) is None and val.__class__.__name__ == "UnionType":
            return str(val)
        
        try:
            json.dumps(val)
            return val
        except TypeError:
            return str(val)
    
    @staticmethod
    def _call_get_desc_static(cls, lang: str = "zh") -> str | None:
        """
        调用类的 get_desc 静态方法
        """
        func_obj = cls.__dict__.get("get_desc")
        if not isinstance(func_obj, staticmethod):
            return None
        
        fn = func_obj.__func__
        params = list(inspect.signature(fn).parameters)
        try:
            if params == ["lang"]:
                return fn(lang)
            if params == ["self", "lang"]:
                return fn(None, lang)
        except Exception:
            pass
        return None
    
    @staticmethod
    def _param_to_dict(p: inspect.Parameter) -> Dict[str, Any]:
        """把 inspect.Parameter 转成字典"""
        return {
            "name": p.name,
            "default": OperatorToolsService._safe_json_val(p.default),
            "kind": p.kind.name,
        }
    
    @staticmethod
    def _get_method_params(method: Any, skip_first_self: bool = False) -> List[Dict[str, Any]]:
        """提取方法形参"""
        try:
            sig = inspect.signature(method)
            params = list(sig.parameters.values())
            if skip_first_self and params and params[0].name == "self":
                params = params[1:]
            return [OperatorToolsService._param_to_dict(p) for p in params]
        except Exception:
            return []
    
    def _gather_single_operator(self, op_name: str, cls: type, node_index: int) -> Tuple[str, Dict[str, Any]]:
        """收集单个算子的全部信息"""
        # 分类
        category = "unknown"
        if hasattr(cls, "__module__"):
            parts = cls.__module__.split(".")
            if len(parts) >= 3 and parts[0] == "dataflow" and parts[1] == "operators":
                category = parts[2]
        
        # 描述
        description = self._call_get_desc_static(cls, lang="zh") or ""
        
        # 参数
        init_params = self._get_method_params(cls.__init__, skip_first_self=True)
        run_params = self._get_method_params(getattr(cls, "run", None), skip_first_self=True)
        
        info = {
            "node": node_index,
            "name": op_name,
            "description": description,
            "parameter": {
                "init": init_params,
                "run": run_params,
            },
            "required": "",
            "depends_on": [],
            "mode": "",
        }
        return category, info
    
    def dump_all_ops_to_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        遍历 OPERATOR_REGISTRY，构建完整字典并写入 ops.json
        """
        all_ops: Dict[str, List[Dict[str, Any]]] = {}
        default_bucket: List[Dict[str, Any]] = []
        
        idx = 1
        for op_name, cls in OPERATOR_REGISTRY:
            category, info = self._gather_single_operator(op_name, cls, idx)
            all_ops.setdefault(category, []).append(info)
            default_bucket.append(info)
            idx += 1
        
        all_ops["Default"] = default_bucket
        
        try:
            with open(self.ops_json_path, "w", encoding="utf-8") as f:
                json.dump(all_ops, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return all_ops
    
    def ensure_ops_cache(self) -> Dict[str, List[Dict[str, Any]]]:
        """若 ops.json 不存在或为空，则重新生成"""
        if self.ops_json_path.exists():
            try:
                with open(self.ops_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data:
                    return data
            except Exception:
                pass
        return self.dump_all_ops_to_file()
    
    def get_operator_content(self, data_type: str) -> str:
        """
        根据 data_type 返回该类别下所有算子的 JSON 字符串
        """
        all_ops = self.dump_all_ops_to_file()
        
        import copy
        if data_type in all_ops:
            content = copy.deepcopy(all_ops[data_type])
        else:
            content = []
        
        return json.dumps(content, ensure_ascii=False, indent=2)
    
    def get_operator_content_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        返回算子列表（Python对象，不是JSON字符串）
        """
        all_ops = self.dump_all_ops_to_file()
        
        if category and category in all_ops:
            return all_ops[category]
        elif category is None:
            return all_ops.get("Default", [])
        else:
            return []
    
    def get_operator_source_by_name(self, operator_name: str) -> str:
        """根据算子名称获取算子的源码"""
        try:
            for name, cls in OPERATOR_REGISTRY:
                if name == operator_name:
                    try:
                        source_code = inspect.getsource(cls)
                        return source_code
                    except Exception as e:
                        return f"# 无法获取源码: {e}"
            
            return f"# 未找到算子 '{operator_name}'，请检查名称是否正确。"
        except Exception as e:
            return f"# 获取算子源码时发生错误: {e}"
    
    def get_prompt_sources_of_operator(self, op_name: str) -> Dict[str, str]:
        """获取 operator 的 prompt_templates 的源码，并随机获取2个示例"""
        cls = OPERATOR_REGISTRY.get(op_name)
        if cls is None:
            raise KeyError(f"Operator {op_name} not found in registry")
        
        if getattr(cls, "ALLOWED_PROMPTS", None):
            prompt_classes = cls.ALLOWED_PROMPTS
        else:
            raise ValueError(f"Operator {op_name} has no ALLOWED_PROMPTS")
        
        if len(prompt_classes) == 0:
            raise ValueError(f"Operator {op_name} has no prompt_templates")
        if len(prompt_classes) == 1:
            sample_classes = prompt_classes
        else:
            sample_classes = random.sample(prompt_classes, min(2, len(prompt_classes)))
        
        out = {}
        for c in sample_classes:
            try:
                out[c.__name__] = inspect.getsource(c)
            except OSError:
                out[c.__name__] = "# 源码不可用（可能是C扩展/找不到源码/zip导入）"
        return out
    
    # ============ RAG 检索部分 ============
    
    @staticmethod
    def _call_openai_embedding_api(
        texts: List[str],
        model_name: str = "text-embedding-ada-002",
        base_url: str = "https://api.openai.com/v1/embeddings",
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> np.ndarray:
        """调用 OpenAI API 获取文本向量"""
        if api_key is None:
            api_key = os.getenv("DF_API_KEY")
        if not api_key:
            raise RuntimeError("必须提供 OpenAI API-Key，可通过参数或环境变量 DF_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        vecs: List[List[float]] = []
        with httpx.Client(timeout=timeout) as client:
            for t in texts:
                resp = client.post(
                    base_url,
                    headers=headers,
                    json={"model": model_name, "input": t},
                )
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(f"调用 OpenAI embedding 失败: {e}\n{resp.text}") from e
                
                try:
                    data = resp.json()
                    vec = data["data"][0]["embedding"]
                except Exception as e:
                    raise RuntimeError(f"解析返回 JSON 失败: {resp.text}") from e
                
                vecs.append(vec)
        
        arr = np.asarray(vecs, dtype=np.float32)
        faiss.normalize_L2(arr)
        return arr
    
    def get_operators_by_rag(
        self,
        search_queries: Union[str, List[str]],
        category: Optional[str] = None,
        top_k: int = 5,
        model_name: str = "text-embedding-3-small",
        base_url: str = "http://123.129.219.111:3000/v1/embeddings",
        api_key: Optional[str] = None,
    ) -> Union[List[str], List[List[str]]]:
        """
        通过 RAG 检索算子
        
        Args:
            search_queries: 单个查询字符串或查询列表
            category: 算子类别，None 表示读取全部
            top_k: 每个查询返回 top-k 结果
            model_name: embedding 模型
            base_url: API 地址
            api_key: API 密钥
        
        Returns:
            单查询返回 List[str]，多查询返回 List[List[str]]
        """
        # 检查索引缓存
        faiss_index_path = self.resource_dir / f"faiss_{category or 'all'}.index"
        
        searcher = RAGOperatorSearch(
            ops_json_path=str(self.ops_json_path),
            category=category,
            faiss_index_path=str(faiss_index_path) if faiss_index_path else None,
            model_name=model_name,
            base_url=base_url,
            api_key=api_key or os.getenv("DF_API_KEY"),
        )
        
        return searcher.search(search_queries, top_k=top_k)


class RAGOperatorSearch:
    """RAG 算子检索类，支持向量持久化和批量查询"""
    
    def __init__(
        self,
        ops_json_path: str,
        category: Optional[str] = None,
        faiss_index_path: Optional[str] = None,
        model_name: str = "text-embedding-ada-002",
        base_url: str = "https://api.openai.com/v1/embeddings",
        api_key: Optional[str] = None,
    ):
        self.ops_json_path = ops_json_path
        self.category = category
        self.faiss_index_path = faiss_index_path
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        
        self.index = None
        self.ops_list = []
        
        self._load_or_build_index()
    
    def _load_operators(self) -> List[Dict]:
        """加载算子数据"""
        with open(self.ops_json_path, "r", encoding="utf-8") as f:
            all_ops = json.load(f)
        
        if self.category:
            ops = all_ops.get(self.category, [])
        else:
            ops = []
            for cat, op_list in all_ops.items():
                ops.extend(op_list)
        
        return ops
    
    def _load_or_build_index(self):
        """加载或构建 FAISS 索引"""
        import pickle
        
        # 检查是否可以复用索引
        if self.faiss_index_path and os.path.exists(self.faiss_index_path):
            meta_path = self.faiss_index_path + ".meta"
            if os.path.exists(meta_path):
                self.index = faiss.read_index(self.faiss_index_path)
                with open(meta_path, "rb") as f:
                    self.ops_list = pickle.load(f)
                return
        
        # 重新构建索引
        self.ops_list = self._load_operators()
        
        if not self.ops_list:
            raise ValueError("没有找到任何算子数据！")
        
        # 生成文本描述
        texts = [f"{op['name']} {op.get('description', '')}" for op in self.ops_list]
        
        # 调用 API 获取向量
        embeddings = OperatorToolsService._call_openai_embedding_api(
            texts,
            model_name=self.model_name,
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # 构建 FAISS 索引
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        
        # 保存索引
        if self.faiss_index_path:
            os.makedirs(os.path.dirname(self.faiss_index_path) or ".", exist_ok=True)
            faiss.write_index(self.index, self.faiss_index_path)
            with open(self.faiss_index_path + ".meta", "wb") as f:
                pickle.dump(self.ops_list, f)
    
    def search(
        self,
        queries: Union[str, List[str]],
        top_k: int = 5
    ) -> Union[List[str], List[List[str]]]:
        """检索最相关的算子"""
        # 统一处理为列表
        is_single = isinstance(queries, str)
        if is_single:
            queries = [queries]
        
        # 批量获取 query 向量
        query_vecs = OperatorToolsService._call_openai_embedding_api(
            queries,
            model_name=self.model_name,
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # 检索
        D, I = self.index.search(query_vecs, top_k)
        
        # 组织结果
        results = []
        for i, indices in enumerate(I):
            matched_ops = [self.ops_list[idx]["name"] for idx in indices]
            results.append(matched_ops)
        
        return results[0] if is_single else results


# 全局实例
_operator_tools_service = OperatorToolsService()
