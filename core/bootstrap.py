from pathlib import Path
import yaml

from core.cache_policy import build_cache_layout
from core.cache_runtime import apply_cache_env

config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"

with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

project_root = Path(__file__).resolve().parents[1]

layout = build_cache_layout(project_root, config)

apply_cache_env(layout)

print("[bootstrap] cache system initialized")