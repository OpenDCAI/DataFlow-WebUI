import os
import re
import yaml
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

try:
    from dataflow.utils.text2sql.database_manager import DatabaseManager
except Exception:
    DatabaseManager = None  # type: ignore


def _safe_filename(name: str) -> str:
    name = os.path.basename(name or "database.sqlite")
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "database.sqlite"


class Text2SQLDatabaseRegistry:
    """
    Registry Yaml Format:
    {
      "{db_id}": {
        "name": "xxx",
        "file_name": "xxx.sqlite",
        "path": "data/sqlite_dbs/{db_id}/xxx.sqlite",
        "uploaded_at": "...",
        "size": 12345
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
        try:
            with open(file_path, "rb") as f:
                header = f.read(16)
            if not header.startswith(b"SQLite format 3\x00"):
                raise ValueError("Uploaded file is not a valid SQLite database")
        except Exception as e:
            raise

    def upload_sqlite_file(self, filename: str, file_bytes: bytes, name: Optional[str] = None, description: Optional[str] = None) -> str:
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
            "description": description
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
        data = self._get_all() or {}
        if db_id not in data:
            return False
        if name:
            data[db_id]["name"] = name
        self._write_all(data)
        return True

    def get_manager(self, selected_db_ids: Optional[List[str]] = None):
        """
        Return usable DataFlow DatabaseManager
        """
        if DatabaseManager is None:
            raise RuntimeError("dataflow.utils.text2sql.DatabaseManager is not available in this environment")

        if selected_db_ids is not None:
            mgr = DatabaseManager(db_type="sqlite", config={"root_path": self.sqlite_root})
            allow = set(selected_db_ids)
            mgr.databases = {db_id: info for db_id, info in mgr.databases.items() if db_id in allow}
            return mgr

        return DatabaseManager(db_type="sqlite", config={"root_path": self.sqlite_root})


