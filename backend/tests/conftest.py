"""
pytest 配置文件
提供共享的 fixtures
"""
import os
import pytest
from app.services.task_registry import TaskRegistry


@pytest.fixture
def test_registry_path(tmp_path):
    """提供临时的注册表文件路径"""
    return str(tmp_path / "test_task_registry.yaml")


@pytest.fixture
def task_registry(test_registry_path):
    """创建一个任务注册表实例，测试后自动清理"""
    registry = TaskRegistry(path=test_registry_path)
    yield registry
    # 清理：测试后删除文件
    if os.path.exists(test_registry_path):
        os.remove(test_registry_path)


@pytest.fixture
def sample_task_data():
    """提供示例任务数据"""
    return {
        "dataset_id": "test_dataset_123",
        "executor_name": "TestPipeline",
        "executor_type": "pipeline",
        "meta": {"test": "true"}
    }


@pytest.fixture
def created_task(task_registry, sample_task_data):
    """创建一个任务并返回"""
    return task_registry.create(sample_task_data)

