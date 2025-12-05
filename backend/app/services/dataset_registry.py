import yaml, os, hashlib
import json
from typing import Dict, List
from app.core.config import settings
import pandas

class DatasetRegistry:
    def __init__(self, path: str | None = None):
        self.path = path or settings.DATA_REGISTRY
        self._ensure()

    def _ensure(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump({"datasets": {}}, f, allow_unicode=True)

    def _read(self) -> Dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"datasets": {}}

    def _write(self, data: Dict):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _count_file_entries(self, file_path: str) -> int:
        """统计文件中的条目数量"""
        # 根据文件类型使用不同的方法计算条目数
        file_ext = file_path.split('.')[-1].lower()
        
        try:
            if file_ext in ['csv', 'jsonl', 'txt', 'log']:
                # 对于文本类文件，按行计数
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return sum(1 for _ in f)
            elif file_ext == 'json':
                # 对于JSON文件，尝试加载并计算
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return len(data)
                    elif isinstance(data, dict):
                        # 如果是字典，返回键的数量
                        return len(data)
                    else:
                        return 1  # 单个值
            else:
                # 对于其他类型文件，默认为1个条目
                return 1
        except Exception:
            # 出错时返回0
            return 0
    
    def list(self) -> List[Dict]:
        """返回所有数据集列表，每个数据集包含条目数和文件大小信息"""
        datasets = list(self._read()["datasets"].values())
        return datasets
    
    def _load_file_hash(self, file_path: str) -> str:
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_or_update(self, ds: Dict):
        data = self._read()
        # 计算一个稳定 id（基于路径）
        ds_id = hashlib.md5(ds["root"].encode("utf-8")).hexdigest()[:10]
        ds["id"] = ds_id
        try: 
            ds["hash"] = self._load_file_hash(ds["root"])
            
            # 计算文件大小（字节）
            ds["file_size"] = os.path.getsize(ds["root"])
            
            # 计算文件条目数
            ds["num_samples"] = self._count_file_entries(ds["root"])
            
        except Exception:
            raise FileNotFoundError(f"Cannot read file at {ds['root']}")
        
        ds['type'] = ds.get('root','').split('.')[-1].lower()
        ds["added_at"] = pandas.Timestamp.now().isoformat()
        
        # 覆盖或新增
        datasets = data.get("datasets",{})
        datasets[ds_id] = ds
        data["datasets"] = datasets
        self._write(data)
        return ds

    def get(self, ds_id: str) -> Dict | None:
        return self._read()["datasets"].get(ds_id)
    
    def remove(self, ds_id: str):
        data = self._read()
        datasets = data.get("datasets", {})
        if ds_id in datasets:
            del datasets[ds_id]
            data["datasets"] = datasets
            self._write(data)
            return True
        return False
    
    def preview(self, ds_id: str, num_lines: int = 5) -> Dict:
        """获取数据集文件的前几行内容预览，支持json、jsonl和parquet格式
        
        Args:
            ds_id: 数据集ID
            num_lines: 要预览的行数
            
        Returns:
            包含预览内容的字典，格式为{"preview": str, "file_type": str, "is_supported": bool}
        """
        ds = self.get(ds_id)
        if not ds:
            raise FileNotFoundError(f"Dataset with id {ds_id} not found")
        
        file_path = ds["root"]
        file_type = ds.get("type", "").lower()
        
        # 检查是否支持预览的文件类型
        supported_types = ["json", "jsonl", "parquet"]
        is_supported = file_type in supported_types
        
        preview_content = ""
        if is_supported:
            try:
                if file_type == "jsonl":
                    # 对于jsonl文件，读取前num_lines行
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            if i >= num_lines:
                                break
                            preview_content += line
                elif file_type == "json":
                    # 对于json文件，读取整个文件并尝试格式化
                    with open(file_path, "r", encoding="utf-8") as f:
                        import json
                        data = json.load(f)
                        if isinstance(data, list):
                            # 如果是列表，只取前num_lines个元素
                            preview_data = data[:num_lines]
                        else:
                            # 如果是字典，直接使用
                            preview_data = data
                        # 使用indent=2格式化JSON
                        preview_content = json.dumps(preview_data, indent=2, ensure_ascii=False)
                elif file_type == "parquet":
                    # 对于parquet文件，使用pandas读取前num_lines行
                    import pandas as pd
                    df = pd.read_parquet(file_path, nrows=num_lines)
                    preview_content = df.to_json(orient="records", indent=2, ensure_ascii=False)
            except Exception as e:
                preview_content = f"Error reading file: {str(e)}"
                is_supported = False
        
        return {
            "preview": preview_content,
            "file_type": file_type,
            "is_supported": is_supported
        }

_DATASET_REGISTRY = DatasetRegistry()