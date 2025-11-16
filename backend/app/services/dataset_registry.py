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

_DATASET_REGISTRY = DatasetRegistry()