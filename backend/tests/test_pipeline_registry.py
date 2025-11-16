"""
Pipeline注册表功能测试

使用 pytest 运行:
    pytest tests/test_pipeline_registry.py -v
    或
    pytest tests/test_pipeline_registry.py::test_create_pipeline -v  # 运行单个测试
"""
import pytest
from typing import Dict, Any
from app.services.pipeline_registry import PipelineRegistry
from app.schemas.pipelines import (
    PipelineIn,
    PipelineConfig,
    PipelineOperator,
    PipelineExecutionResult,
    ExecutionStatus
)


# 测试数据 fixtures
@pytest.fixture
def pipeline_registry():
    """创建一个新的PipelineRegistry实例"""
    return PipelineRegistry()


@pytest.fixture
def sample_pipeline_operator():
    """创建一个示例PipelineOperator"""
    return PipelineOperator(
        name="data_processor",
        params={"batch_size": 32, "shuffle": True}
    )


@pytest.fixture
def sample_pipeline_config(sample_pipeline_operator):
    """创建一个示例PipelineConfig"""
    return PipelineConfig(
        input_dataset="test_dataset_123",
        operators=[sample_pipeline_operator],
        run_config={"max_workers": 4, "timeout": 3600}
    )


@pytest.fixture
def sample_pipeline_data(sample_pipeline_config):
    """创建示例Pipeline输入数据"""
    return PipelineIn(
        name="测试Pipeline",
        config=sample_pipeline_config,
        tags=["test", "nlp"]
    )


@pytest.fixture
def created_pipeline(pipeline_registry, sample_pipeline_data):
    """创建并返回一个已创建的Pipeline"""
    return pipeline_registry.create_pipeline(sample_pipeline_data)


class TestPipelineRegistry:
    """Pipeline注册表测试类"""

    def test_create_registry(self):
        """测试创建Pipeline注册表实例"""
        registry = PipelineRegistry()
        assert registry is not None
        assert hasattr(registry, '_pipeline_registry')
        assert hasattr(registry, '_execution_results')

    def test_create_pipeline(self, pipeline_registry, sample_pipeline_data):
        """测试创建Pipeline"""
        pipeline = pipeline_registry.create_pipeline(sample_pipeline_data)
        
        assert pipeline is not None
        # 简单验证返回对象的类型，确保它有预期的属性
        assert hasattr(pipeline, 'id')
        assert hasattr(pipeline, 'name')
        assert hasattr(pipeline, 'config')
        assert hasattr(pipeline, 'tags')
        assert hasattr(pipeline, 'created_at')
        assert hasattr(pipeline, 'updated_at')
        assert hasattr(pipeline, 'status')
        
        assert pipeline.id is not None
        assert pipeline.name == sample_pipeline_data.name
        assert pipeline.config.input_dataset == sample_pipeline_data.config.input_dataset
        assert pipeline.tags == sample_pipeline_data.tags
        assert pipeline.created_at is not None
        assert pipeline.updated_at is not None
        assert pipeline.status == ExecutionStatus.queued

    def test_get_pipeline(self, pipeline_registry, created_pipeline):
        """测试获取Pipeline详情"""
        pipeline_id = created_pipeline.id
        retrieved_pipeline = pipeline_registry.get_pipeline(pipeline_id)
        
        assert retrieved_pipeline is not None
        assert retrieved_pipeline.id == pipeline_id
        assert retrieved_pipeline.name == created_pipeline.name
        assert retrieved_pipeline.config.input_dataset == created_pipeline.config.input_dataset

    def test_get_nonexistent_pipeline(self, pipeline_registry):
        """测试获取不存在的Pipeline"""
        pipeline = pipeline_registry.get_pipeline("nonexistent_id")
        assert pipeline is None

    def test_update_pipeline(self, pipeline_registry, created_pipeline, sample_pipeline_data):
        """测试更新Pipeline"""
        pipeline_id = created_pipeline.id
        
        # 修改数据
        updated_data = PipelineIn(
            name="更新后的Pipeline",
            config=sample_pipeline_data.config,
            tags=["updated", "test"]
        )
        
        updated_pipeline = pipeline_registry.update_pipeline(pipeline_id, updated_data)
        
        assert updated_pipeline.id == pipeline_id
        assert updated_pipeline.name == "更新后的Pipeline"
        assert updated_pipeline.tags == ["updated", "test"]
        assert updated_pipeline.created_at == created_pipeline.created_at  # 创建时间不变
        assert updated_pipeline.updated_at != created_pipeline.updated_at  # 更新时间改变

    def test_update_nonexistent_pipeline(self, pipeline_registry, sample_pipeline_data):
        """测试更新不存在的Pipeline"""
        with pytest.raises(ValueError):
            pipeline_registry.update_pipeline("nonexistent_id", sample_pipeline_data)

    def test_delete_pipeline(self, pipeline_registry, created_pipeline):
        """测试删除Pipeline"""
        pipeline_id = created_pipeline.id
        
        # 确认Pipeline存在
        assert pipeline_registry.get_pipeline(pipeline_id) is not None
        
        # 删除Pipeline
        result = pipeline_registry.delete_pipeline(pipeline_id)
        assert result is True
        
        # 确认Pipeline已删除
        assert pipeline_registry.get_pipeline(pipeline_id) is None

    def test_delete_nonexistent_pipeline(self, pipeline_registry):
        """测试删除不存在的Pipeline"""
        result = pipeline_registry.delete_pipeline("nonexistent_id")
        assert result is False

    def test_list_pipelines(self, pipeline_registry, sample_pipeline_data):
        """测试列出所有Pipelines"""
        # 创建多个Pipelines
        pipeline1 = pipeline_registry.create_pipeline(sample_pipeline_data)
        pipeline2 = pipeline_registry.create_pipeline(
            PipelineIn(
                name="Pipeline 2",
                config=sample_pipeline_data.config,
                tags=["tag2"]
            )
        )
        
        all_pipelines = pipeline_registry.list_pipelines()
        assert len(all_pipelines) >= 2
        
        # 验证创建的Pipelines都在列表中
        pipeline_ids = [p.id for p in all_pipelines]
        assert pipeline1.id in pipeline_ids
        assert pipeline2.id in pipeline_ids

    def test_start_execution_with_pipeline_id(self, pipeline_registry, created_pipeline):
        """测试使用pipeline_id开始执行"""
        execution_id, pipeline_config, initial_result = pipeline_registry.start_execution(
            pipeline_id=created_pipeline.id
        )
        
        assert execution_id is not None
        assert pipeline_config.input_dataset == created_pipeline.config.input_dataset
        assert initial_result.execution_id == execution_id
        assert initial_result.status == ExecutionStatus.queued

    def test_start_execution_with_config(self, pipeline_registry, sample_pipeline_config):
        """测试使用config开始执行"""
        execution_id, pipeline_config, initial_result = pipeline_registry.start_execution(
            config=sample_pipeline_config
        )
        
        assert execution_id is not None
        assert pipeline_config.input_dataset == sample_pipeline_config.input_dataset
        assert initial_result.execution_id == execution_id
        assert initial_result.status == ExecutionStatus.queued

    def test_start_execution_without_required_params(self, pipeline_registry):
        """测试不提供必要参数的情况"""
        with pytest.raises(ValueError):
            pipeline_registry.start_execution()

    def test_start_execution_with_nonexistent_pipeline_id(self, pipeline_registry):
        """测试使用不存在的pipeline_id"""
        with pytest.raises(ValueError):
            pipeline_registry.start_execution(pipeline_id="nonexistent_id")

    def test_get_execution_result(self, pipeline_registry, created_pipeline):
        """测试获取执行结果"""
        execution_id, _, _ = pipeline_registry.start_execution(
            pipeline_id=created_pipeline.id
        )
        
        # 初始时应该能获取到状态为queued的结果
        result = pipeline_registry.get_execution_result(execution_id)
        assert result is not None
        assert result.execution_id == execution_id
        assert result.status == ExecutionStatus.queued

    def test_get_nonexistent_execution_result(self, pipeline_registry):
        """测试获取不存在的执行结果"""
        result = pipeline_registry.get_execution_result("nonexistent_execution_id")
        assert result is None

    def test_list_executions(self, pipeline_registry, created_pipeline, sample_pipeline_config):
        """测试列出所有执行记录"""
        # 创建多个执行记录
        execution_id1, _, _ = pipeline_registry.start_execution(
            pipeline_id=created_pipeline.id
        )
        execution_id2, _, _ = pipeline_registry.start_execution(
            config=sample_pipeline_config
        )
        
        all_executions = pipeline_registry.list_executions()
        assert len(all_executions) >= 2
        
        # 验证创建的执行记录都在列表中
        execution_ids = [e.execution_id for e in all_executions]
        assert execution_id1 in execution_ids
        assert execution_id2 in execution_ids


class TestPipelineRegistryEdgeCases:
    """Pipeline注册表边界情况测试"""

    def test_create_pipeline_with_complex_config(self, pipeline_registry):
        """测试使用复杂配置创建Pipeline"""
        # 创建多个算子的配置
        complex_config = PipelineConfig(
            input_dataset="complex_dataset",
            operators=[
                PipelineOperator(name="operator1", params={"param1": "value1"}),
                PipelineOperator(name="operator2", params={"param2": "value2"}),
                PipelineOperator(name="operator3", params={"param3": "value3"})
            ],
            run_config={"complex_param": {"nested": "value"}}
        )
        
        pipeline_data = PipelineIn(
            name="复杂Pipeline",
            config=complex_config,
            tags=["complex", "test"]
        )
        
        pipeline = pipeline_registry.create_pipeline(pipeline_data)
        assert pipeline is not None
        assert len(pipeline.config.operators) == 3
        assert pipeline.config.run_config == {"complex_param": {"nested": "value"}}

    def test_pipeline_lifecycle(self, pipeline_registry, sample_pipeline_data, sample_pipeline_config):
        """测试完整的Pipeline生命周期"""
        # 1. 创建Pipeline
        pipeline = pipeline_registry.create_pipeline(sample_pipeline_data)
        pipeline_id = pipeline.id
        
        # 2. 获取Pipeline
        retrieved_pipeline = pipeline_registry.get_pipeline(pipeline_id)
        assert retrieved_pipeline is not None
        
        # 3. 更新Pipeline
        updated_data = PipelineIn(
            name="更新后的Pipeline",
            config=sample_pipeline_config,
            tags=["updated"]
        )
        updated_pipeline = pipeline_registry.update_pipeline(pipeline_id, updated_data)
        assert updated_pipeline.name == "更新后的Pipeline"
        
        # 4. 执行Pipeline
        execution_id, _, _ = pipeline_registry.start_execution(pipeline_id=pipeline_id)
        
        # 5. 删除Pipeline
        delete_result = pipeline_registry.delete_pipeline(pipeline_id)
        assert delete_result is True

    def test_concurrent_pipeline_creation(self, pipeline_registry, sample_pipeline_data):
        """测试并发创建多个Pipelines"""
        pipelines = []
        for i in range(5):
            pipeline = pipeline_registry.create_pipeline(
                PipelineIn(
                    name=f"Pipeline_{i}",
                    config=sample_pipeline_data.config,
                    tags=[f"tag_{i}"]
                )
            )
            pipelines.append(pipeline)
        
        # 验证所有Pipelines都有唯一ID
        pipeline_ids = [p.id for p in pipelines]
        assert len(pipeline_ids) == len(set(pipeline_ids))  # 确保ID唯一
        
        # 验证所有Pipelines都能被获取
        for pipeline in pipelines:
            retrieved = pipeline_registry.get_pipeline(pipeline.id)
            assert retrieved is not None
            assert retrieved.id == pipeline.id


@pytest.mark.asyncio
async def test_execute_pipeline_task(pipeline_registry, sample_pipeline_config):
    """测试异步执行Pipeline任务"""
    execution_id = "test_execution_async"
    
    # 执行任务
    await pipeline_registry.execute_pipeline_task(execution_id, sample_pipeline_config)
    
    # 获取执行结果
    result = pipeline_registry.get_execution_result(execution_id)
    
    assert result is not None
    assert result.execution_id == execution_id
    assert result.status in [ExecutionStatus.completed, ExecutionStatus.failed]
    assert len(result.logs) > 0


@pytest.mark.parametrize("status_value", ["queued", "running", "completed", "failed"])
@pytest.mark.asyncio
async def test_different_execution_statuses(pipeline_registry, sample_pipeline_config, status_value):
    """参数化测试：测试不同的执行状态"""
    execution_id = f"test_status_{status_value}"
    
    # 先创建一个初始状态的执行结果
    initial_result = PipelineExecutionResult(
        execution_id=execution_id,
        status=status_value,
        output={},
        logs=[f"测试状态: {status_value}"]
    )
    pipeline_registry._execution_results[execution_id] = initial_result
    
    # 获取并验证状态
    result = pipeline_registry.get_execution_result(execution_id)
    assert result.status == status_value
