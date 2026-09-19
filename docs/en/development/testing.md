# Testing

**Language / 语言:** English · [中文](../../development/testing.md)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable ".[dev]"
python -m pytest --cov
```

CI also runs `python -m build` and `twine check`. Tests must not require real
Telegraph / image-host credentials; mock network boundaries and use temporary
files.
