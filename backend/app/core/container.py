# Registry Container

class AppContainer:
    """
    这里主要是为了解决之前直接在module里面全局初始化对象时，各个Registry被实例化的顺序不可控的问题。
    """
    def __init__(self):
        self.dataset_registry = None
        self.operator_registry = None
        self.prompt_registry = None
        self.serving_registry = None
        self.task_registry = None
        self.pipeline_registry = None
        self.text2sql_database_registry = None
        self.text2sql_database_manager_registry = None
        self.dataset_visualize_service = None

    def init(self):
        from app.services.dataset_registry import DatasetRegistry, VisualizeDatasetService
        from app.services.pipeline_registry import PipelineRegistry
        from app.services.operator_registry import OperatorRegistry
        from app.services.prompt_registry import PromptRegistry
        from app.services.serving_registry import ServingRegistry
        from app.services.task_registry import TaskRegistry
        from app.services.text2sql_database_registry import Text2SQLDatabaseRegistry, Text2SQLDatabaseManagerRegistry


        # 初始化顺序在这里完全由你控制
        self.dataset_registry = DatasetRegistry()
        self.dataset_visualize_service = VisualizeDatasetService()
        self.operator_registry = OperatorRegistry()
        self.prompt_registry = PromptRegistry()
        self.serving_registry = ServingRegistry()
        self.task_registry = TaskRegistry()
        self.pipeline_registry = PipelineRegistry()
        self.text2sql_database_registry = Text2SQLDatabaseRegistry()
        self.text2sql_database_manager_registry = Text2SQLDatabaseManagerRegistry()



# 创建一个全局 container（模块级单例）
container = AppContainer()