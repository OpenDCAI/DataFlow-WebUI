import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import container
from app.api.v1.endpoints import text2sql_database
from app.services.text2sql_database_registry import (
    Text2SQLDatabaseRegistry,
    Text2SQLDatabaseManagerRegistry,
)
from app.services.dataflow_engine import DataFlowEngine


@pytest.fixture
def text2sql_test_app(tmp_path: Path) -> FastAPI:
    """
    Build a minimal FastAPI app only mounting the text2sql database endpoints,
    and redirect registries to tmp_path to avoid touching real data/ directories.
    """
    sqlite_root = tmp_path / "sqlite_dbs"
    sqlite_root.mkdir(parents=True, exist_ok=True)

    db_registry_path = tmp_path / "text2sql_database_registry.yaml"
    mgr_registry_path = tmp_path / "text2sql_database_manager_registry.yaml"

    container.text2sql_database_registry = Text2SQLDatabaseRegistry(
        path=str(db_registry_path),
        sqlite_root=str(sqlite_root),
    )
    container.text2sql_database_manager_registry = Text2SQLDatabaseManagerRegistry(
        path=str(mgr_registry_path)
    )

    app = FastAPI()
    app.include_router(text2sql_database.router, prefix="/api/v1/text2sql_database")
    app.include_router(text2sql_database.manager_router, prefix="/api/v1/text2sql_database_manager")
    return app


@pytest.fixture
def client(text2sql_test_app: FastAPI) -> TestClient:
    return TestClient(text2sql_test_app)


def _make_sqlite_bytes(tmp_path: Path) -> bytes:
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / "db.sqlite"
    con = sqlite3.connect(str(p))
    try:
        con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
        con.execute("INSERT INTO t(name) VALUES ('alice')")
        con.commit()
    finally:
        con.close()
    return p.read_bytes()

def _upload_db(client: TestClient, filename: str, content: bytes, name: str | None = None, description: str | None = None) -> str:
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    r = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": (filename, content, "application/octet-stream")},
        data=data,
    )
    assert r.status_code == 200
    return r.json()["data"]["id"]


def test_sqlite_upload_list_get_delete(client: TestClient, tmp_path: Path):
    b = _make_sqlite_bytes(tmp_path)
    db_id = _upload_db(client, "test.sqlite", b, name="mydb", description="desc")

    r = client.get("/api/v1/text2sql_database/")
    assert r.status_code == 200
    items = r.json()["data"]
    assert any(x["id"] == db_id for x in items)
    # response is sanitized (no filesystem path)
    assert all("path" not in x for x in items)

    r = client.get(f"/api/v1/text2sql_database/{db_id}")
    assert r.status_code == 200
    item = r.json()["data"]
    assert item["id"] == db_id
    assert "path" not in item

    r = client.delete(f"/api/v1/text2sql_database/{db_id}")
    assert r.status_code == 200

    r = client.get(f"/api/v1/text2sql_database/{db_id}")
    assert r.status_code == 404


def test_sqlite_upload_rejects_non_sqlite_content(client: TestClient):
    r = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("fake.sqlite", b"not a sqlite file", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_sqlite_upload_rejects_wrong_extension_even_if_sqlite(client: TestClient, tmp_path: Path):
    b = _make_sqlite_bytes(tmp_path)
    r = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("db.txt", b, "application/octet-stream")},
    )
    assert r.status_code == 400


def test_sqlite_get_and_delete_nonexistent(client: TestClient):
    r = client.get("/api/v1/text2sql_database/does_not_exist")
    assert r.status_code == 404
    r = client.delete("/api/v1/text2sql_database/does_not_exist")
    assert r.status_code == 404


def test_database_manager_crud(client: TestClient, tmp_path: Path):
    b1 = _make_sqlite_bytes(tmp_path / "one")
    b2 = _make_sqlite_bytes(tmp_path / "two")

    db1 = _upload_db(client, "one.sqlite", b1)
    db2 = _upload_db(client, "two.sqlite", b2)

    r = client.get("/api/v1/text2sql_database_manager/classes")
    assert r.status_code == 200
    classes = r.json()["data"]
    assert isinstance(classes, list) and classes
    assert any(
        c["cls_name"] == "DatabaseManager"
        and any(p["name"] == "selected_db_ids" for p in c.get("params", []))
        for c in classes
    )

    r = client.post(
        "/api/v1/text2sql_database_manager/",
        json={
            "name": "mgr1",
            "cls_name": "DatabaseManager",
            "db_type": "sqlite",
            "selected_db_ids": [db1, db2],
            "description": "d",
        },
    )
    assert r.status_code == 200
    mgr_id = r.json()["data"]["id"]

    r = client.get("/api/v1/text2sql_database_manager/")
    assert r.status_code == 200
    mgrs = r.json()["data"]
    assert any(m["id"] == mgr_id for m in mgrs)

    r = client.get(f"/api/v1/text2sql_database_manager/{mgr_id}")
    assert r.status_code == 200
    mgr = r.json()["data"]
    assert mgr["id"] == mgr_id
    assert mgr["selected_db_ids"] == [db1, db2]

    r = client.put(
        f"/api/v1/text2sql_database_manager/{mgr_id}",
        json={"name": "mgr2", "selected_db_ids": [db1], "description": "d2"},
    )
    assert r.status_code == 200

    r = client.get(f"/api/v1/text2sql_database_manager/{mgr_id}")
    assert r.status_code == 200
    mgr = r.json()["data"]
    assert mgr["name"] == "mgr2"
    assert mgr["selected_db_ids"] == [db1]

    r = client.delete(f"/api/v1/text2sql_database_manager/{mgr_id}")
    assert r.status_code == 200

    r = client.get(f"/api/v1/text2sql_database_manager/{mgr_id}")
    assert r.status_code == 404


def test_database_manager_rejects_unknown_db_id(client: TestClient):
    r = client.post(
        "/api/v1/text2sql_database_manager/",
        json={
            "name": "mgr_bad",
            "cls_name": "DatabaseManager",
            "db_type": "sqlite",
            "selected_db_ids": ["does_not_exist"],
        },
    )
    assert r.status_code == 400


def test_database_manager_update_rejects_unknown_db_id(client: TestClient, tmp_path: Path):
    db1 = _upload_db(client, "one.sqlite", _make_sqlite_bytes(tmp_path / "one"))
    mgr_id = client.post(
        "/api/v1/text2sql_database_manager/",
        json={"name": "mgr", "cls_name": "DatabaseManager", "db_type": "sqlite", "selected_db_ids": [db1]},
    ).json()["data"]["id"]
    r = client.put(
        f"/api/v1/text2sql_database_manager/{mgr_id}",
        json={"selected_db_ids": ["does_not_exist"]},
    )
    assert r.status_code == 400


def test_database_manager_update_and_delete_nonexistent(client: TestClient):
    r = client.put("/api/v1/text2sql_database_manager/does_not_exist", json={"name": "x"})
    assert r.status_code == 404
    r = client.delete("/api/v1/text2sql_database_manager/does_not_exist")
    assert r.status_code == 404


def test_database_manager_subset_is_respected_by_runtime_manager(client: TestClient, tmp_path: Path):
    """
    More realistic flow:
    - upload multiple sqlite dbs
    - create a manager config selecting a subset
    - build the real DatabaseManager via registry.get_manager(selected_db_ids)
      and assert the databases mapping is filtered correctly
    """
    b1 = _make_sqlite_bytes(tmp_path / "db1")
    b2 = _make_sqlite_bytes(tmp_path / "db2")
    b3 = _make_sqlite_bytes(tmp_path / "db3")

    db1 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("db1.sqlite", b1, "application/octet-stream")},
    ).json()["data"]["id"]
    db2 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("db2.sqlite", b2, "application/octet-stream")},
    ).json()["data"]["id"]
    db3 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("db3.sqlite", b3, "application/octet-stream")},
    ).json()["data"]["id"]

    r = client.post(
        "/api/v1/text2sql_database_manager/",
        json={
            "name": "mgr_subset",
            "cls_name": "DatabaseManager",
            "db_type": "sqlite",
            "selected_db_ids": [db1, db3],
        },
    )
    assert r.status_code == 200
    mgr_id = r.json()["data"]["id"]

    cfg = container.text2sql_database_manager_registry._get(mgr_id)
    assert cfg is not None
    assert cfg["selected_db_ids"] == [db1, db3]

    # Runtime manager filtered
    mgr_subset = container.text2sql_database_registry.get_manager(cfg["selected_db_ids"])
    assert set(mgr_subset.databases.keys()) == {db1, db3}
    assert db2 not in mgr_subset.databases

    # Runtime manager unfiltered (all)
    mgr_all = container.text2sql_database_registry.get_manager(None)
    assert {db1, db2, db3}.issubset(set(mgr_all.databases.keys()))


def test_database_manager_empty_selection_results_in_empty_runtime_manager(client: TestClient):
    mgr_id = client.post(
        "/api/v1/text2sql_database_manager/",
        json={"name": "mgr_empty", "cls_name": "DatabaseManager", "db_type": "sqlite", "selected_db_ids": []},
    ).json()["data"]["id"]
    cfg = container.text2sql_database_manager_registry._get(mgr_id)
    mgr = container.text2sql_database_registry.get_manager(cfg["selected_db_ids"])
    assert set(mgr.databases.keys()) == set()


def test_engine_database_manager_injection_supports_manager_id_and_list(client: TestClient, tmp_path: Path, monkeypatch):
    """
    Integration-ish test (simulates real runtime wiring without calling external LLMs):
    - Use API to upload multiple sqlite DBs
    - Create DatabaseManager config selecting a subset (manager_id)
    - Run DataFlowEngine.run() with a dummy operator to verify that:
      - database_manager value == manager_id -> engine looks up config and passes selected_db_ids into get_manager()
      - database_manager value == list[db_id] -> engine passes that list into get_manager() directly
    """

    # 1) Prepare sqlite dbs via API (real registry + files)
    b1 = _make_sqlite_bytes(tmp_path / "e2e_db1")
    b2 = _make_sqlite_bytes(tmp_path / "e2e_db2")
    b3 = _make_sqlite_bytes(tmp_path / "e2e_db3")

    db1 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("e2e_db1.sqlite", b1, "application/octet-stream")},
    ).json()["data"]["id"]
    db2 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("e2e_db2.sqlite", b2, "application/octet-stream")},
    ).json()["data"]["id"]
    db3 = client.post(
        "/api/v1/text2sql_database/upload",
        files={"file": ("e2e_db3.sqlite", b3, "application/octet-stream")},
    ).json()["data"]["id"]

    mgr_id = client.post(
        "/api/v1/text2sql_database_manager/",
        json={
            "name": "mgr_e2e",
            "cls_name": "DatabaseManager",
            "db_type": "sqlite",
            "selected_db_ids": [db1, db3],
        },
    ).json()["data"]["id"]

    # 2) Monkeypatch runtime dependencies to avoid external side effects (no disk IO for FileStorage)

    class _DummyDatasetRegistry:
        def get(self, dataset_id: str):
            return {"root": "dummy_input_root"}

    container.dataset_registry = _DummyDatasetRegistry()

    class _DummyStorage:
        def __init__(self, *args, **kwargs):
            pass

        def step(self):
            return object()

    # Patch FileStorage used by DataFlowEngine
    import app.services.dataflow_engine as df_engine_mod

    monkeypatch.setattr(df_engine_mod, "FileStorage", _DummyStorage)

    # Patch operator lookup to return a dummy operator class
    from dataflow.utils.text2sql.database_manager import DatabaseManager

    observed_db_sets: list[set[str]] = []

    class DummyOp:
        def __init__(self, database_manager=None):
            # Ensure engine injected a real DatabaseManager instance and it is filtered correctly.
            assert isinstance(database_manager, DatabaseManager)
            observed_db_sets.append(set(database_manager.databases.keys()))

        def run(self, storage=None, **kwargs):
            assert storage is not None
            return None

    monkeypatch.setattr(df_engine_mod.OPERATOR_REGISTRY, "get", lambda name: DummyOp)

    # 3) Run engine with database_manager == manager_id
    engine = DataFlowEngine()
    engine.run(
        {
            "input_dataset": "ds1",
            "operators": [
                {
                    "name": "DummyOp",
                    "params": {
                        "init": [{"name": "database_manager", "value": mgr_id}],
                        "run": [],
                    },
                }
            ],
        },
        execution_id="exec1",
    )

    # 4) Run engine with database_manager == list[db_id]
    engine.run(
        {
            "input_dataset": "ds1",
            "operators": [
                {
                    "name": "DummyOp",
                    "params": {
                        "init": [{"name": "database_manager", "value": [db1, db2]}],
                        "run": [],
                    },
                }
            ],
        },
        execution_id="exec2",
    )

    assert observed_db_sets[0] == {db1, db3}
    assert observed_db_sets[1] == {db1, db2}


def test_engine_database_manager_missing_manager_id_raises(client: TestClient, monkeypatch):
    """
    If pipeline references a manager_id that doesn't exist, engine should fail fast.
    """
    from app.services.dataflow_engine import DataFlowEngine
    import app.services.dataflow_engine as df_engine_mod

    class _DummyDatasetRegistry:
        def get(self, dataset_id: str):
            return {"root": "dummy_input_root"}

    container.dataset_registry = _DummyDatasetRegistry()

    class _DummyStorage:
        def __init__(self, *args, **kwargs):
            pass

        def step(self):
            return object()

    monkeypatch.setattr(df_engine_mod, "FileStorage", _DummyStorage)

    class DummyOp:
        def __init__(self, database_manager=None):
            self.database_manager = database_manager

        def run(self, storage=None, **kwargs):
            return None

    monkeypatch.setattr(df_engine_mod.OPERATOR_REGISTRY, "get", lambda name: DummyOp)

    engine = DataFlowEngine()
    result = engine.run(
        {
            "input_dataset": "ds1",
            "operators": [
                {
                    "name": "DummyOp",
                    "params": {"init": [{"name": "database_manager", "value": "no_such_id"}], "run": []},
                }
            ],
        },
        execution_id="exec_missing_mgr",
    )
    assert result["status"] == "failed"
    assert "database_manager config not found" in str(result["output"].get("original_error", ""))


def test_engine_database_manager_none_uses_all(client: TestClient, tmp_path: Path, monkeypatch):
    """
    If database_manager param is None, engine should inject a manager containing all dbs.
    """
    # Upload 2 dbs
    db1 = _upload_db(client, "a.sqlite", _make_sqlite_bytes(tmp_path / "a"))
    db2 = _upload_db(client, "b.sqlite", _make_sqlite_bytes(tmp_path / "b"))

    import app.services.dataflow_engine as df_engine_mod
    from dataflow.utils.text2sql.database_manager import DatabaseManager

    class _DummyDatasetRegistry:
        def get(self, dataset_id: str):
            return {"root": "dummy_input_root"}

    container.dataset_registry = _DummyDatasetRegistry()

    class _DummyStorage:
        def __init__(self, *args, **kwargs):
            pass

        def step(self):
            return object()

    monkeypatch.setattr(df_engine_mod, "FileStorage", _DummyStorage)

    observed: list[set[str]] = []

    class DummyOp:
        def __init__(self, database_manager=None):
            assert isinstance(database_manager, DatabaseManager)
            observed.append(set(database_manager.databases.keys()))

        def run(self, storage=None, **kwargs):
            return None

    monkeypatch.setattr(df_engine_mod.OPERATOR_REGISTRY, "get", lambda name: DummyOp)

    engine = DataFlowEngine()
    engine.run(
        {
            "input_dataset": "ds1",
            "operators": [
                {
                    "name": "DummyOp",
                    "params": {"init": [{"name": "database_manager", "value": None}], "run": []},
                }
            ],
        },
        execution_id="exec_none_mgr",
    )

    assert {db1, db2}.issubset(observed[0])


