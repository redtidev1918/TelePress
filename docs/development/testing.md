# 测试

**Language / 语言:** [中文](testing.md) · [English](../en/development/testing.md)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable ".[dev]"
python -m pytest --cov
```

CI 会额外跑 `python -m build` 与 `twine check`。测试不能依赖真实 Telegraph / 图床凭据；
网络边界用 mock，文件相关用临时文件。
