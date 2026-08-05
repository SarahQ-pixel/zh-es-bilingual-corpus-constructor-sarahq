from pathlib import Path
import sys


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def setup_python_path():
    project_root = str(get_project_root())

    if project_root not in sys.path:
        sys.path.insert(0, project_root)