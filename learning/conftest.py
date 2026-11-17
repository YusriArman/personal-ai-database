"""Each module's tests receive `target`: your exercise.py by default, or the reference
solution.py when LEARNING_TARGET=solution is set."""

import importlib.util
import os
from pathlib import Path

import pytest


@pytest.fixture
def target(request):
    name = os.environ.get("LEARNING_TARGET", "exercise")
    path = Path(request.fspath).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{path.parent.name}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
