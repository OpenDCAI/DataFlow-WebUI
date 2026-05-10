# Registration Rules

## Registry Requirement

Each operator class must use:

```python
@OPERATOR_REGISTRY.register()
```

Required imports:

```python
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.core import OperatorABC
```

ZH: 每个 operator 类都必须带 `@OPERATOR_REGISTRY.register()` 装饰器并使用上述导入。

## Package Import Rule

To make registration effective after import:
- package-level `__init__.py` should auto-import operator modules, or
- tests/import paths should import operator modules directly.

Preferred pattern:
- keep auto importer in `<package_name>/__init__.py`
- keep `operators/<type>/__init__.py` explicit and simple

ZH: 推荐在包根 `__init__.py` 做自动导入，以确保注册生效。

## Test Rule

Registry test must validate:
- class name appears in `OPERATOR_REGISTRY`
- `OPERATOR_REGISTRY.get(class_name)` resolves to generated class

ZH: 注册测试至少要覆盖“存在性 + 可解析到类对象”。
