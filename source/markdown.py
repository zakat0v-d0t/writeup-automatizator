import os
from jinja2 import Environment, FileSystemLoader
from .models import WriteupContext
from .exceptions import MarkdownGenerationError

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

class MarkdownService:
    def generate(self, context: WriteupContext, json_path: str) -> str:
        try:
            template = env.get_template("default.md")
            content = template.render(**context.model_dump())
            
            output_path = json_path.replace(".json", ".md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return output_path
        except Exception as e:
            raise MarkdownGenerationError(f"Ошибка генерации MD: {e}")
