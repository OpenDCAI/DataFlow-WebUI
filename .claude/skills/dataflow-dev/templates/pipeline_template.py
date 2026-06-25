"""
DataFlow Pipeline 骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

风格：Style B（普通类，无 PipelineABC 继承）
适用：绝大多数实际 DataFlow Pipeline，支持 compile() 特性的场景改用 Style A

注意：
  - storage 在 __init__ 中声明（不要在 forward() 中创建）
  - 每个算子调用传 storage=self.storage.step()
  - 算子成员变量命名带 _stepN 后缀
  - LLM Serving 在 __init__ 中统一声明
  - API key 通过环境变量注入，不硬编码
"""

import os

from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request

# ── 按需 import 算子 ──────────────────────────────────────────────────────
# from dataflow.operators.general_text import <OperatorA>, <OperatorB>
# from dataflow.operators.text_sft import <OperatorC>
# from dataflow.operators.reasoning import <OperatorD>
# ─────────────────────────────────────────────────────────────────────────────


class <PipelineClassName>:
    """
    <Pipeline 功能一句话描述>

    数据流：<input_field> → [步骤1] → <mid_field> → [步骤2] → <output_field>
    """

    def __init__(self):
        # ── Storage：在 __init__ 中声明，不在 forward() 中创建 ──────────
        self.storage = FileStorage(
            first_entry_file_name="<path/to/input.jsonl>",  # 替换为实际路径
            cache_path="./cache",
            file_name_prefix="dataflow_cache_step",
            cache_type="jsonl",
        )

        # ── LLM Serving：在 __init__ 中统一声明 ──────────────────────────
        self.llm_serving = APILLMServing_request(
            api_url=os.environ.get("DF_API_URL", "https://api.openai.com/v1"),
            key_name_of_api_key="DF_API_KEY",     # 对应环境变量名
            model_name=os.environ.get("DF_MODEL_NAME", "gpt-4o"),
            max_workers=200,  # 自建/代理 API 推荐 200+；官方 API 推荐 50-100
        )

        # ── 算子成员变量：带 _stepN 后缀，N 为执行顺序 ──────────────────
        # self.op_step1 = <OperatorA>(
        #     llm_serving=self.llm_serving,
        #     # 配置参数...
        # )
        # self.op_step2 = <OperatorB>(
        #     llm_serving=self.llm_serving,
        # )

    def forward(self):
        """按顺序执行所有算子。每次 run() 传 storage=self.storage.step()"""

        # ── Step 1 ────────────────────────────────────────────────────────
        # self.op_step1.run(
        #     storage=self.storage.step(),
        #     input_<field>="<input_col_name>",
        #     output_<field>="<step1_output_col>",
        # )

        # ── Step 2 ────────────────────────────────────────────────────────
        # self.op_step2.run(
        #     storage=self.storage.step(),
        #     input_<field>="<step1_output_col>",  # 与上一步 output 对齐
        #     output_<field>="<final_output_col>",
        # )

        pass


if __name__ == "__main__":
    # 运行前确保以下环境变量已设置：
    #   export DF_API_KEY="your-api-key"
    #   export DF_API_URL="https://api.example.com/v1"
    #   export DF_MODEL_NAME="your-model-name"

    pipeline = <PipelineClassName>()
    pipeline.forward()


# ─────────────────────────────────────────────────────────────────────────────
# Style A 参考（继承 PipelineABC，支持 compile() / DAG 执行）
# 适用场景：需要可视化 DAG、断点续传（BatchedPipelineABC）的场景
#
# from dataflow.pipeline.base import PipelineABC
#
# class MyPipeline(PipelineABC):
#     def __init__(self):
#         super().__init__()
#         self.storage = FileStorage(...)
#         self.llm_serving = APILLMServing_request(...)
#         self.op_step1 = OperatorA(llm_serving=self.llm_serving)
#         self.op_step2 = OperatorB(llm_serving=self.llm_serving)
#
#     def forward(self):
#         self.op_step1.run(storage=self.storage.step(), ...)
#         self.op_step2.run(storage=self.storage.step(), ...)
#
# ─────────────────────────────────────────────────────────────────────────────
