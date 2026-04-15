"""
DataFlow 算子骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

模板类型：通用算子（支持 LLM 驱动和非 LLM 两种模式）
"""

from typing import TYPE_CHECKING

from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.operators.base import OperatorABC

# 仅 LLM 驱动算子需要：
# from dataflow.serving import LLMServingABC


# ─── 如果算子需要自定义 Prompt，在此定义或 import ───────────────────────────
# from dataflow.prompts.base import PromptABC, DIYPromptABC, PROMPT_REGISTRY
# from dataflow.operators.base import prompt_restrict
#
# @PROMPT_REGISTRY.register()
# class <ClassName>Prompt(DIYPromptABC):
#     def build_prompt(self, text: str) -> str:
#         return f"请处理以下文本：\n{text}"
# ─────────────────────────────────────────────────────────────────────────────


@OPERATOR_REGISTRY.register()
# 若算子需要限制 Prompt 类型，取消下行注释，并确保此装饰器紧贴类定义
# @prompt_restrict(<ClassName>Prompt)
class <OperatorClassName>(OperatorABC):
    """
    <算子功能一句话描述>

    类型：<filter / generate / refine / eval>
    模块：<general_text / text_sft / reasoning / code>
    """

    def __init__(
        self,
        # ── LLM 驱动算子需要 ──────────────────────────────
        # llm_serving,        # 成员名必须为 self.llm_serving
        # ── 配置参数放此处（不放 run()）──────────────────
        # param_a: int = 10,
        # param_b: str = "default",
    ):
        super().__init__()  # 初始化 self.logger

        # ── LLM 驱动算子 ──────────────────────────────────
        # self.llm_serving = llm_serving  # 成员名必须是 self.llm_serving

        # ── 其他成员变量 ──────────────────────────────────
        # self.param_a = param_a
        # self.param_b = param_b

    @staticmethod
    def get_desc(lang: str = "zh") -> str:
        """
        返回算子描述字符串（纯 str，不是 dict）。
        必须同时支持 zh 和 en。
        """
        if lang == "zh":
            return "<算子中文描述，一句话>"
        return "<Operator English description, one sentence>"

    def run(
        self,
        storage,                          # DataFlowStorage，必须是第一个参数
        input_<field_name>: str = "<default_input_col>",   # 输入列名，必须以 input_ 开头
        output_<field_name>: str = "<default_output_col>", # 输出列名，必须以 output_ 开头
        # 若有多个输入/输出列，继续添加 input_xxx / output_xxx 参数
    ):
        """
        算子主逻辑。

        Args:
            storage: DataFlowStorage 实例
            input_<field_name>: 输入数据列名
            output_<field_name>: 输出结果列名

        Returns:
            list[str]: 输出列名列表
        """
        # ── 1. 读取数据 ───────────────────────────────────
        df = storage.read("dataframe")
        self.logger.info(f"读取到 {len(df)} 条数据")

        # ── 2. 核心处理逻辑 ──────────────────────────────
        results = []
        for idx, row in df.iterrows():
            text = row[input_<field_name>]

            # 容错处理：跳过空值
            if not text or not str(text).strip():
                results.append("")
                continue

            try:
                # ── 非 LLM 算子：直接处理 ──────────────────
                result = self._process(text)

                # ── LLM 算子：调用 LLM ────────────────────
                # response = self.llm_serving.chat(
                #     messages=[{"role": "user", "content": prompt}]
                # )
                # result = self._parse_response(response)

                results.append(result)

            except Exception as e:
                self.logger.warning(f"第 {idx} 条数据处理失败：{e}")
                results.append("")  # 失败时给默认值，不中断整体流程

        # ── 3. 写回结果 ──────────────────────────────────
        df[output_<field_name>] = results
        storage.write(df)

        self.logger.info(f"算子执行完成，输出列：{output_<field_name>}")

        # ── 4. 返回输出列名列表 ──────────────────────────
        return [output_<field_name>]

    # ── 辅助方法（可选）────────────────────────────────────────────────────
    def _process(self, text: str) -> str:
        """非 LLM 处理逻辑的具体实现"""
        raise NotImplementedError

    # def _parse_response(self, response: str) -> str:
    #     """LLM 响应解析（参考 dev_notes.md §1.8 容错模板 A/B/C/D）"""
    #     raise NotImplementedError


# ─── LLM 容错模板参考（选择适合的模板粘贴到 _parse_response 中）─────────────
#
# 模板 A：直接使用原始文本
# try:
#     result = response.strip()
# except Exception:
#     result = ""
#
# 模板 B：JSON 解析
# import json
# try:
#     data = json.loads(response)
#     result = data.get("result", "")
# except (json.JSONDecodeError, AttributeError):
#     result = ""
#
# 模板 C：正则提取
# import re
# match = re.search(r"答案[:：]\s*(.+)", response, re.DOTALL)
# result = match.group(1).strip() if match else ""
#
# 模板 D：数字评分
# try:
#     score = float(response.strip())
#     result = score
# except (ValueError, AttributeError):
#     result = 0.0
# ─────────────────────────────────────────────────────────────────────────────


# ─── CoT 模型输出 <think> 标签剥离（若算子处理 CoT 模型输出）──────────────
# import re
# def strip_think_tag(text: str) -> str:
#     """剥离 <think>...</think> 标签，保留标签外的内容"""
#     return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
# ─────────────────────────────────────────────────────────────────────────────
