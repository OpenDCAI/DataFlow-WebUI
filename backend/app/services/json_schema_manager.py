import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger as log
from app.core.config import settings


# --- Path definitions ---
BACKEND_DIR = Path(__file__).parent.parent.parent
SCHEMAS_DIR = BACKEND_DIR / settings.RESOURCE_DIR / "schemas"
SCHEMAS_FILE = SCHEMAS_DIR / "schemas.json"


class JsonSchemaManager:
    """
    Manages JSON Schema CRUD operations with file-based persistence.
    """
    
    def __init__(self):
        """Initialize schema manager and ensure schemas directory exists."""
        self._ensure_storage()
        self.schemas: Dict[str, Any] = self._load_schemas()
    
    def _ensure_storage(self):
        """Ensure the schemas directory and file exist."""
        SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
        if not SCHEMAS_FILE.exists():
            SCHEMAS_FILE.write_text(json.dumps({}))
    
    def _load_schemas(self) -> Dict[str, Any]:
        """Load all schemas from file."""
        try:
            if SCHEMAS_FILE.exists():
                content = SCHEMAS_FILE.read_text()
                return json.loads(content) if content.strip() else {}
            return {}
        except Exception as e:
            log.warning(f"Failed to load schemas: {e}")
            return {}
    
    def _save_schemas(self) -> None:
        """Save all schemas to file."""
        try:
            SCHEMAS_FILE.write_text(json.dumps(self.schemas, ensure_ascii=False, indent=2))
        except Exception as e:
            log.error(f"Failed to save schemas: {e}")
            raise
    
    def create(self, name: str, description: str, schema: str, example: str) -> Dict[str, Any]:
        """
        Create a new JSON schema.
        """
        schema_id = f"schema_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        schema_obj = {
            "id": schema_id,
            "name": name,
            "description": description,
            "schema": schema,
            "example": example,
            "created_at": now,
            "updated_at": now
        }
        
        self.schemas[schema_id] = schema_obj
        self._save_schemas()
        log.info(f"Created schema: {schema_id}")
        return schema_obj
    
    def get(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Get a schema by ID."""
        return self.schemas.get(schema_id)
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all schemas."""
        return list(self.schemas.values())
    
    def update(self, schema_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update a schema by ID.
        Only provided fields are updated.
        """
        if schema_id not in self.schemas:
            return None
        
        schema_obj = self.schemas[schema_id]
        
        # Update only provided fields
        if "name" in kwargs and kwargs["name"] is not None:
            schema_obj["name"] = kwargs["name"]
        if "description" in kwargs and kwargs["description"] is not None:
            schema_obj["description"] = kwargs["description"]
        if "schema" in kwargs and kwargs["schema"] is not None:
            schema_obj["schema"] = kwargs["schema"]
        if "example" in kwargs and kwargs["example"] is not None:
            schema_obj["example"] = kwargs["example"]
        
        schema_obj["updated_at"] = datetime.utcnow().isoformat()
        self._save_schemas()
        log.info(f"Updated schema: {schema_id}")
        return schema_obj
    
    def delete(self, schema_id: str) -> bool:
        """Delete a schema by ID."""
        if schema_id in self.schemas:
            del self.schemas[schema_id]
            self._save_schemas()
            log.info(f"Deleted schema: {schema_id}")
            return True
        return False
    
    def delete_by_name(self, name: str) -> bool:
        """Delete all schemas with a given name."""
        to_delete = [sid for sid, s in self.schemas.items() if s.get("name") == name]
        for sid in to_delete:
            del self.schemas[sid]
        if to_delete:
            self._save_schemas()
            log.info(f"Deleted {len(to_delete)} schemas with name: {name}")
        return len(to_delete) > 0
