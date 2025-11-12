import yaml, os, hashlib
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

    def list(self) -> List[Dict]:
        return self._read()["datasets"].values()
    
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
        except Exception:
            raise FileNotFoundError(f"Cannot read file at {ds['root']}")
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
