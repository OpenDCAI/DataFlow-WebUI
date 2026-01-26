"""
任务注册表功能测试

使用 pytest 运行:
    pytest tests/test_task_registry.py -v
    或
    pytest tests/test_task_registry.py::test_create_task -v  # 运行单个测试
"""
import pytest
from app.services.task_registry import TaskRegistry


class TestTaskRegistry:
    """任务注册表测试类"""

    def test_create_registry(self, test_registry_path):
        """测试创建任务注册表实例"""
        registry = TaskRegistry(path=test_registry_path)
        assert registry is not None
        assert registry.path == test_registry_path

    def test_create_task(self, task_registry, sample_task_data):
        """测试创建任务"""
        task = task_registry.create(sample_task_data)
        
        assert task is not None
        assert "id" in task
        assert task["dataset_id"] == sample_task_data["dataset_id"]
        assert task["executor_name"] == sample_task_data["executor_name"]
        assert task["executor_type"] == sample_task_data["executor_type"]
        assert task["status"] == "pending"
        assert "created_at" in task
        assert task["created_at"] is not None

    def test_get_task(self, task_registry, created_task):
        """测试获取任务详情"""
        task_id = created_task["id"]
        retrieved_task = task_registry.get(task_id)
        
        assert retrieved_task is not None
        assert retrieved_task["id"] == task_id
        assert retrieved_task["executor_name"] == created_task["executor_name"]
        assert retrieved_task["dataset_id"] == created_task["dataset_id"]

    def test_get_nonexistent_task(self, task_registry):
        """测试获取不存在的任务"""
        task = task_registry.get("nonexistent_id")
        assert task is None

    def test_update_task_status_to_running(self, task_registry, created_task):
        """测试更新任务状态为 running"""
        task_id = created_task["id"]
        updated_task = task_registry.update(task_id, {"status": "running"})
        
        assert updated_task["status"] == "running"
        assert updated_task["started_at"] is not None
        assert "started_at" in updated_task

    def test_update_task_status_to_success(self, task_registry, created_task):
        """测试完成任务（成功）"""
        task_id = created_task["id"]
        
        # 先设置为 running
        task_registry.update(task_id, {"status": "running"})
        
        # 再设置为 success
        completed_task = task_registry.update(task_id, {
            "status": "success",
            "output_id": "test_output_456"
        })
        
        assert completed_task["status"] == "success"
        assert completed_task["output_id"] == "test_output_456"
        assert completed_task["finished_at"] is not None

    def test_update_task_status_to_failed(self, task_registry, created_task):
        """测试任务失败状态"""
        task_id = created_task["id"]
        error_msg = "测试错误信息"
        
        failed_task = task_registry.update(task_id, {
            "status": "failed",
            "error_message": error_msg
        })
        
        assert failed_task["status"] == "failed"
        assert failed_task["error_message"] == error_msg
        assert failed_task["finished_at"] is not None

    def test_list_all_tasks(self, task_registry, sample_task_data):
        """测试列出所有任务"""
        # 创建多个任务
        task_registry.create(sample_task_data)
        task_registry.create({**sample_task_data, "dataset_id": "dataset_2"})
        task_registry.create({**sample_task_data, "dataset_id": "dataset_3"})
        
        all_tasks = task_registry.list()
        assert len(all_tasks) >= 3

    def test_list_tasks_by_status(self, task_registry, sample_task_data):
        """测试按状态过滤任务列表"""
        # 创建多个不同状态的任务
        task1 = task_registry.create(sample_task_data)
        task2 = task_registry.create({**sample_task_data, "dataset_id": "dataset_2"})
        task3 = task_registry.create({**sample_task_data, "dataset_id": "dataset_3"})
        
        # 设置不同状态
        task_registry.update(task1["id"], {"status": "running"})
        task_registry.update(task2["id"], {"status": "success"})
        # task3 保持 pending
        
        # 测试过滤
        pending_tasks = task_registry.list(status="pending")
        running_tasks = task_registry.list(status="running")
        success_tasks = task_registry.list(status="success")
        
        assert len(pending_tasks) >= 1
        assert len(running_tasks) >= 1
        assert len(success_tasks) >= 1
        
        # 验证状态正确
        assert all(t["status"] == "pending" for t in pending_tasks)
        assert all(t["status"] == "running" for t in running_tasks)
        assert all(t["status"] == "success" for t in success_tasks)

    def test_list_tasks_by_executor_type(self, task_registry, sample_task_data):
        """测试按执行器类型过滤任务列表"""
        # 创建不同类型的任务
        task_registry.create({**sample_task_data, "executor_type": "pipeline"})
        task_registry.create({**sample_task_data, "executor_type": "operator"})
        
        pipeline_tasks = task_registry.list(executor_type="pipeline")
        operator_tasks = task_registry.list(executor_type="operator")
        
        assert len(pipeline_tasks) >= 1
        assert len(operator_tasks) >= 1
        assert all(t["executor_type"] == "pipeline" for t in pipeline_tasks)
        assert all(t["executor_type"] == "operator" for t in operator_tasks)

    def test_get_statistics(self, task_registry, sample_task_data):
        """测试获取统计信息"""
        # 创建多个不同状态的任务
        task1 = task_registry.create({**sample_task_data, "executor_type": "pipeline"})
        task2 = task_registry.create({**sample_task_data, "executor_type": "operator"})
        task3 = task_registry.create({**sample_task_data, "executor_type": "pipeline"})
        
        # 设置不同状态
        task_registry.update(task1["id"], {"status": "running"})
        task_registry.update(task2["id"], {"status": "success"})
        task_registry.update(task3["id"], {"status": "failed", "error_message": "测试失败"})
        
        stats = task_registry.get_statistics()
        
        # 验证统计信息
        assert "total" in stats
        assert stats["total"] >= 3
        assert "pending" in stats
        assert "running" in stats
        assert stats["running"] >= 1
        assert "success" in stats
        assert stats["success"] >= 1
        assert "failed" in stats
        assert stats["failed"] >= 1
        assert "by_executor_type" in stats
        assert "pipeline" in stats["by_executor_type"]
        assert "operator" in stats["by_executor_type"]

    def test_delete_task(self, task_registry, created_task):
        """测试删除任务"""
        task_id = created_task["id"]
        
        # 确认任务存在
        assert task_registry.get(task_id) is not None
        
        # 删除任务
        result = task_registry.delete(task_id)
        assert result is True
        
        # 确认任务已删除
        assert task_registry.get(task_id) is None

    def test_task_lifecycle(self, task_registry, sample_task_data):
        """测试完整的任务生命周期"""
        # 1. 创建任务
        task = task_registry.create(sample_task_data)
        assert task["status"] == "pending"
        task_id = task["id"]
        
        # 2. 开始任务
        task = task_registry.update(task_id, {"status": "running"})
        assert task["status"] == "running"
        assert task["started_at"] is not None
        
        # 3. 完成任务
        task = task_registry.update(task_id, {
            "status": "success",
            "output_id": "final_output"
        })
        assert task["status"] == "success"
        assert task["output_id"] == "final_output"
        assert task["finished_at"] is not None
        
        # 4. 验证时间逻辑
        assert task["created_at"] <= task["started_at"]
        assert task["started_at"] <= task["finished_at"]


class TestTaskRegistryEdgeCases:
    """任务注册表边界情况测试"""

    def test_create_task_with_minimal_data(self, task_registry):
        """测试使用最少必需数据创建任务"""
        minimal_data = {
            "dataset_id": "test_dataset",
            "executor_name": "TestExecutor",
            "executor_type": "pipeline"
        }
        task = task_registry.create(minimal_data)
        
        assert task is not None
        assert task["dataset_id"] == minimal_data["dataset_id"]
        assert task["status"] == "pending"

    def test_update_nonexistent_task(self, task_registry):
        """测试更新不存在的任务"""
        result = task_registry.update("nonexistent_id", {"status": "running"})
        assert result is None

    def test_multiple_status_transitions(self, task_registry, created_task):
        """测试多次状态转换"""
        task_id = created_task["id"]
        
        # pending -> running
        task = task_registry.update(task_id, {"status": "running"})
        assert task["status"] == "running"
        
        # running -> failed
        task = task_registry.update(task_id, {
            "status": "failed",
            "error_message": "Something went wrong"
        })
        assert task["status"] == "failed"
        assert task["error_message"] == "Something went wrong"

    def test_concurrent_task_creation(self, task_registry, sample_task_data):
        """测试并发创建多个任务"""
        tasks = []
        for i in range(10):
            task = task_registry.create({
                **sample_task_data,
                "dataset_id": f"dataset_{i}"
            })
            tasks.append(task)
        
        # 验证所有任务都有唯一ID
        task_ids = [t["id"] for t in tasks]
        assert len(task_ids) == len(set(task_ids))  # 确保ID唯一
        
        # 验证所有任务都能被获取
        for task in tasks:
            retrieved = task_registry.get(task["id"])
            assert retrieved is not None
            assert retrieved["id"] == task["id"]


@pytest.mark.parametrize("executor_type", ["pipeline", "operator"])
def test_create_different_executor_types(task_registry, sample_task_data, executor_type):
    """参数化测试：测试创建不同执行器类型的任务"""
    task_data = {**sample_task_data, "executor_type": executor_type}
    task = task_registry.create(task_data)
    
    assert task["executor_type"] == executor_type


@pytest.mark.parametrize("status", ["pending", "running", "success", "failed"])
def test_filter_by_status(task_registry, sample_task_data, status):
    """参数化测试：测试按不同状态过滤"""
    # 创建任务并设置状态
    task = task_registry.create(sample_task_data)
    if status != "pending":
        task_registry.update(task["id"], {"status": status})
    
    # 过滤并验证
    filtered_tasks = task_registry.list(status=status)
    assert len(filtered_tasks) >= 1
    assert all(t["status"] == status for t in filtered_tasks)

