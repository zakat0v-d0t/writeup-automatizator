import os
import yaml
from .exceptions import WriteupError

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wup_config.yaml")

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        raise WriteupError(f"Ошибка чтения конфига: {e}")
