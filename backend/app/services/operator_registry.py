from dataflow.utils.registry import OPERATOR_REGISTRY, PROMPT_REGISTRY

class OperatorRegistry:
    def __init__(self):
        self._op_registry = OPERATOR_REGISTRY
        self._prompt_registry = PROMPT_REGISTRY
        # TODO add whitelist/blacklist mechanism
        self._op_registry._get_all()
        self.op_obj_map = self._op_registry.get_obj_map()
        self.op_to_type = self._op_registry.get_type_of_objects()


    def get_op_list(self, lang: str = "zh") -> list[dict]:
        op_list = []
        for op_name, op_cls in self.op_obj_map.items():
            op_type_category = self.op_to_type.get(op_name, "Unknown/Unknown")
            import loguru
            loguru.logger.info(op_type_category)
            # 三级分类
            _ = op_type_category[0] # 只是表征是算子还是prompt
            type1 = op_type_category[1] if len(op_type_category) > 1 else "Unknown"     # 大类，比如“text2sql”
            type2 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"    # 小类，比如“generate还是啥”

            # 描述
            if hasattr(op_cls, "get_desc") and callable(op_cls.get_desc):
                desc = op_cls.get_desc(lang=lang)
            else:
                desc = "N/A"
            desc = str(desc)

            # prompt template
            allowed_prompt_templates = getattr(op_cls, "ALLOWED_PROMPTS", [])
            allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

            # get parameter info in .run()

            op_info = {
                "name": op_name,
                "type": {
                    "level_1": type1,
                    "level_2": type2
                },
                "description": desc,
                "allowed_prompts": allowed_prompt_templates
            }
            op_list.append(op_info)
        return op_list
    
_op_registry = OperatorRegistry()