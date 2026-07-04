import os
import json
import glob
from .models import WriteupContext
from .exceptions import StorageError

class StorageService:
    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(base_dir) if base_dir else os.getcwd()
        self.writeups_dir = os.path.join(self.base_dir, "writeups")

    def save_json(self, context: WriteupContext, year: str, safe_title: str) -> str:
        try:
            target_dir = os.path.join(self.writeups_dir, year, context.category)
            os.makedirs(target_dir, exist_ok=True)
            
            json_path = os.path.join(target_dir, f"{safe_title}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(context.model_dump_json(indent=4))
            return json_path
        except Exception as e:
            raise StorageError(f"Ошибка сохранения JSON: {e}")

    def load_json(self, json_path: str) -> WriteupContext:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WriteupContext(**data)
        except Exception as e:
            raise StorageError(f"Ошибка чтения JSON: {e}")

    def get_all(self):
        pattern = os.path.join(self.writeups_dir, "**", "*.json")
        json_files = glob.glob(pattern, recursive=True)
        results = []
        for j_path in sorted(json_files):
            try:
                with open(j_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                md_exists = os.path.exists(j_path.replace(".json", ".md"))
                results.append((data, md_exists))
            except Exception as e:
                import logging
                logging.error(f"Ошибка чтения JSON {j_path}: {e}")
                continue
        return results
