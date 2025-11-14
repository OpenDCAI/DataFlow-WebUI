import json
import uuid
import datetime
from typing import List, Optional
from app.core.logger_setup import get_logger
from app.schemas.pipelines import (
    PipelineIn,
    PipelineOut, 
    PipelineConfig, 
    PipelineExecutionResult
)

logger = get_logger(__name__)


class PipelineRegistry:
    def __init__(self):
        self._pipeline_registry = {}
        self._execution_results = {}
    
    def get_current_time(self):
        """获取当前时间的ISO格式字符串"""
        return datetime.datetime.now().isoformat()
    
    def list_pipelines(self) -> List[PipelineOut]:
        """列出所有注册的Pipeline"""
        return list(self._pipeline_registry.values())
    
    def create_pipeline(self, pipeline_data: PipelineIn) -> PipelineOut:
        """创建一个新的Pipeline"""
        # 生成唯一ID
        pipeline_id = str(uuid.uuid4())
        current_time = self.get_current_time()
        
        # 创建PipelineOut对象
        pipeline = PipelineOut(
            id=pipeline_id,
            name=pipeline_data.name,
            config=pipeline_data.config,
            tags=pipeline_data.tags,
            created_at=current_time,
            updated_at=current_time
        )
        
        # 保存到注册表
        self._pipeline_registry[pipeline_id] = pipeline
        logger.info(f"Successfully created pipeline: {pipeline_id} with name: {pipeline_data.name}")
        return pipeline
    
    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineOut]:
        """根据ID获取Pipeline"""
        return self._pipeline_registry.get(pipeline_id)
    
    def update_pipeline(self, pipeline_id: str, pipeline_data: PipelineIn) -> PipelineOut:
        """更新指定的Pipeline"""
        if pipeline_id not in self._pipeline_registry:
            raise ValueError(f"Pipeline with id {pipeline_id} not found")
        
        current_pipeline = self._pipeline_registry[pipeline_id]
        # 更新字段，保留创建时间
        updated_pipeline = PipelineOut(
            id=pipeline_id,
            name=pipeline_data.name,
            config=pipeline_data.config,
            tags=pipeline_data.tags,
            created_at=current_pipeline.created_at,
            updated_at=self.get_current_time()
        )
        
        self._pipeline_registry[pipeline_id] = updated_pipeline
        logger.info(f"Updated pipeline: {pipeline_id}")
        return updated_pipeline
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除指定的Pipeline"""
        if pipeline_id not in self._pipeline_registry:
            return False
        
        del self._pipeline_registry[pipeline_id]
        logger.info(f"Deleted pipeline: {pipeline_id}")
        return True
    
    async def execute_pipeline_task(self, execution_id: str, pipeline_config: PipelineConfig):
        """异步执行Pipeline的任务"""
        logs = []
        output = {}
        status = "running"
        logger.info(f"Starting background execution task for execution_id: {execution_id}")
        
        try:
            # 初始化执行结果
            self._execution_results[execution_id] = PipelineExecutionResult(
                execution_id=execution_id,
                status=status,
                output=output,
                logs=logs
            )
            
            # 记录开始执行
            logs.append(f"[{self.get_current_time()}] Starting pipeline execution")
            logs.append(f"[{self.get_current_time()}] Input dataset: {pipeline_config.input_dataset}")
            logs.append(f"[{self.get_current_time()}] Run config: {json.dumps(pipeline_config.run_config)}")
            
            # 模拟数据加载
            logs.append(f"[{self.get_current_time()}] Loading dataset: {pipeline_config.input_dataset}")
            
            # 按顺序执行算子
            current_data = {"dataset_id": pipeline_config.input_dataset, "data": {}}
            for i, operator in enumerate(pipeline_config.operators):
                logs.append(f"[{self.get_current_time()}] Executing operator {i+1}/{len(pipeline_config.operators)}: {operator.name}")
                logs.append(f"[{self.get_current_time()}] Operator params: {json.dumps(operator.params)}")
                
                try:
                    # 模拟算子执行
                    current_data["data"] = {
                        "operator": operator.name,
                        "params": operator.params,
                        "output": f"Processed by {operator.name}"
                    }
                    logs.append(f"[{self.get_current_time()}] Operator {operator.name} executed successfully")
                except Exception as op_error:
                    error_msg = f"Operator {operator.name} failed: {op_error}"
                    logs.append(f"[{self.get_current_time()}] ERROR: {error_msg}")
                    status = "failed"
                    output["error"] = error_msg
                    break
            
            # 更新执行结果
            if status != "failed":
                status = "completed"
                output["result"] = current_data
                logs.append(f"[{self.get_current_time()}] Pipeline execution completed successfully")
            
        except Exception as e:
            status = "failed"
            error_msg = f"Pipeline execution failed: {e}"
            logs.append(f"[{self.get_current_time()}] ERROR: {error_msg}")
            output["error"] = error_msg
        
        # 保存最终结果
        self._execution_results[execution_id] = PipelineExecutionResult(
            execution_id=execution_id,
            status=status,
            output=output,
            logs=logs
        )
    
    def start_execution(self, pipeline_id: Optional[str] = None, config: Optional[PipelineConfig] = None) -> tuple[str, PipelineExecutionResult]:
        """开始执行Pipeline"""
        # 获取Pipeline配置
        if pipeline_id:
            pipeline = self.get_pipeline(pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline with id {pipeline_id} not found")
            pipeline_config = pipeline.config
            logger.info(f"Executing predefined pipeline: {pipeline_id}")
        else:
            if not config:
                raise ValueError("Either pipeline_id or config must be provided")
            pipeline_config = config
            logger.info("Executing pipeline with provided config")
        
        # 生成执行ID
        execution_id = str(uuid.uuid4())
        
        # 返回初始结果
        initial_result = PipelineExecutionResult(
            execution_id=execution_id,
            status="queued",
            output={},
            logs=[f"[{self.get_current_time()}] Pipeline execution queued"]
        )
        
        return execution_id, pipeline_config, initial_result
    
    def get_execution_result(self, execution_id: str) -> Optional[PipelineExecutionResult]:
        """获取Pipeline执行结果"""
        return self._execution_results.get(execution_id)
    
    def list_executions(self) -> List[PipelineExecutionResult]:
        """列出所有Pipeline执行记录"""
        return list(self._execution_results.values())


# 创建全局服务实例
_PIPELINE_REGISTRY = PipelineRegistry()
