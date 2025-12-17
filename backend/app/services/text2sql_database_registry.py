import os
import re
import yaml
import shutil
import inspect
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.config import settings

try:
    from dataflow.utils.text2sql.database_manager import DatabaseManager
except Exception:
    DatabaseManager = None

try:
    import importlib
    DATABASE_MANAGER_MODULE = importlib.import_module("dataflow.utils.text2sql.database_manager")
except Exception:
    DATABASE_MANAGER_MODULE = None


def _safe_filename(name: str) -> str:
    name = os.path.basename(name or "database.sqlite")
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "database.sqlite"


DATABASE_MANAGER_MODULE_ALL = ["DatabaseManager"]

DATABASE_MANAGER_CLS_REGISTRY: Dict[str, Any] = {}
if DATABASE_MANAGER_MODULE is not None:
    DATABASE_MANAGER_CLS_REGISTRY = {
        cls_name: getattr(DATABASE_MANAGER_MODULE, cls_name)
        for cls_name in DATABASE_MANAGER_MODULE_ALL
        if hasattr(DATABASE_MANAGER_MODULE, cls_name)
    }


class Text2SQLDatabaseRegistry:
    """
    sqlite file registry.

    Registry Yaml Format:
    {
      "{db_id}": {
        "name": "xxx",
        "file_name": "xxx.sqlite",
        "path": "data/sqlite_dbs/{db_id}/xxx.sqlite",
        "uploaded_at": "...",
        "size": 12345,
        "description": "..."
      }
    }
    """

    def __init__(self, path: str | None = None, sqlite_root: str | None = None):
        self.path = path or settings.TEXT2SQL_DATABASE_REGISTRY
        self.sqlite_root = sqlite_root or settings.SQLITE_DB_DIR
        self._ensure()

    def _ensure(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        os.makedirs(self.sqlite_root, exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump({}, f, allow_unicode=True)

    def _get_all(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_all(self, data: Dict[str, Any]):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _get(self, db_id: str) -> Optional[Dict[str, Any]]:
        data = self._get_all()
        item = data.get(db_id)
        if not item:
            return None
        item = dict(item)
        item["id"] = db_id
        return item

    def list(self) -> List[Dict[str, Any]]:
        data = self._get_all()
        result = []
        for k, v in (data or {}).items():
            vv = dict(v or {})
            vv["id"] = k
            result.append(vv)
        return result

    def _validate_sqlite_file(self, file_path: str):
        # 校验sqlite
        with open(file_path, "rb") as f:
            header = f.read(16)
        if not header.startswith(b"SQLite format 3\x00"):
            raise ValueError("Uploaded file is not a valid SQLite database")

    def upload_sqlite_file(
        self,
        filename: str,
        file_bytes: bytes,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        上传并注册sqlite
        """
        if not file_bytes:
            raise ValueError("Empty file")

        safe_name = _safe_filename(filename)
        if not any(safe_name.lower().endswith(ext) for ext in (".db", ".sqlite", ".sqlite3")):
            raise ValueError("Only .db/.sqlite/.sqlite3 files are supported")

        db_id = os.urandom(8).hex()
        db_dir = os.path.join(self.sqlite_root, db_id)
        os.makedirs(db_dir, exist_ok=True)
        dest_path = os.path.join(db_dir, safe_name)

        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        self._validate_sqlite_file(dest_path)

        data = self._get_all() or {}
        data[db_id] = {
            "name": name or os.path.splitext(safe_name)[0],
            "file_name": safe_name,
            "path": dest_path,
            "uploaded_at": datetime.now().isoformat(),
            "size": os.path.getsize(dest_path),
            "description": description,
        }
        self._write_all(data)
        return db_id

    def _delete(self, db_id: str, remove_files: bool = True) -> bool:
        data = self._get_all() or {}
        if db_id not in data:
            return False

        if remove_files:
            db_dir = os.path.join(self.sqlite_root, db_id)
            if os.path.isdir(db_dir):
                shutil.rmtree(db_dir, ignore_errors=True)

        del data[db_id]
        self._write_all(data)
        return True

    def _update(self, db_id: str, name: Optional[str] = None) -> bool:
        """
        改名字.
        """
        data = self._get_all() or {}
        if db_id not in data:
            return False
        if name:
            data[db_id]["name"] = name
        self._write_all(data)
        return True


class Text2SQLDatabaseManagerRegistry:
    """
    DatabaseManager config registry.

    Registry Yaml Format:
    {
      "{mgr_id}": {
        "name": "xxx",
        "cls_name": "DatabaseManager",
        "db_type": "sqlite",
        "selected_db_ids": ["..."],
        "description": "...",
        "created_at": "..."
      }
    }
    """

    def __init__(self, path: str | None = None):
        self.path = path or settings.TEXT2SQL_DATABASE_MANAGER_REGISTRY
        self._ensure()

    def _ensure(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump({}, f, allow_unicode=True)

    def _get_all(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_all(self, data: Dict[str, Any]):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def list(self) -> List[Dict[str, Any]]:
        data = self._get_all()
        result: List[Dict[str, Any]] = []
        for k, v in (data or {}).items():
            vv = dict(v or {})
            vv["id"] = k
            result.append(vv)
        return result

    def _get(self, mgr_id: str) -> Optional[Dict[str, Any]]:
        data = self._get_all()
        item = data.get(mgr_id)
        if not item:
            return None
        item = dict(item)
        item["id"] = mgr_id
        return item

    def _set(
        self,
        name: str,
        cls_name: str,
        db_type: str = "sqlite",
        selected_db_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> str:
        data = self._get_all() or {}
        mgr_id = os.urandom(8).hex()
        data[mgr_id] = {
            "name": name,
            "cls_name": cls_name,
            "db_type": db_type,
            "selected_db_ids": selected_db_ids or [],
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
        self._write_all(data)
        return mgr_id

    def _update(
        self,
        mgr_id: str,
        name: str | None = None,
        selected_db_ids: Optional[List[str]] = None,
        description: str | None = None,
    ) -> bool:
        data = self._get_all() or {}
        if mgr_id not in data:
            return False
        if name is not None:
            data[mgr_id]["name"] = name
        if selected_db_ids is not None:
            data[mgr_id]["selected_db_ids"] = selected_db_ids
        if description is not None:
            data[mgr_id]["description"] = description
        self._write_all(data)
        return True

    def _delete(self, mgr_id: str) -> bool:
        data = self._get_all() or {}
        if mgr_id not in data:
            return False
        del data[mgr_id]
        self._write_all(data)
        return True

    def get_manager_classes(self) -> List[Dict[str, Any]]:
        """
        获取所有可用的DatabaseManager类定义.
        """
        result: List[Dict[str, Any]] = []

        for cls_name, cls in (DATABASE_MANAGER_CLS_REGISTRY or {}).items():
            params: List[Dict[str, Any]] = []
            init_method = getattr(cls, "__init__", None)
            if init_method:
                try:
                    sig = inspect.signature(init_method)
                    for name, param in sig.parameters.items():
                        if name == "self":
                            continue
                        if param.annotation != inspect.Parameter.empty:
                            if hasattr(param.annotation, "__name__"):
                                p_type = param.annotation.__name__
                            else:
                                p_type = str(param.annotation)
                        else:
                            p_type = "Any"

                        default_val = None
                        required = True
                        if param.default != inspect.Parameter.empty:
                            default_val = param.default
                            required = False

                        params.append(
                            {
                                "name": name,
                                "type": p_type,
                                "default_value": default_val,
                                "required": required,
                            }
                        )
                except ValueError:
                    pass

            params.append(
                {
                    "name": "selected_db_ids",
                    "type": "List[str]",
                    "default_value": [],
                    "required": False,
                }
            )

            result.append({"cls_name": cls_name, "params": params})

        if not result:
            result = [
                {
                    "cls_name": "DatabaseManager",
                    "params": [
                        {"name": "db_type", "type": "str", "default_value": "sqlite", "required": True},
                        {"name": "config", "type": "dict", "default_value": {}, "required": True},
                        {"name": "selected_db_ids", "type": "List[str]", "default_value": [], "required": False},
                    ],
                }
            ]

        return result


