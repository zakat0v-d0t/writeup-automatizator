import os
import json
import stat
import glob
from jinja2 import Environment, FileSystemLoader
import markdown
from telegraph import Telegraph

from .models import WriteupContext

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

class WriteupManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(base_dir) if base_dir else os.getcwd()
        self.writeups_dir = os.path.join(self.base_dir, "writeups")

    def save_writeup(self, context: WriteupContext, year: str) -> str:
        safe_title = context.title.lower().replace(" ", "_").replace("'", "").replace('"', '')
        target_dir = os.path.join(self.writeups_dir, year, context.category)
        os.makedirs(target_dir, exist_ok=True)
        
        json_path = os.path.join(target_dir, f"{safe_title}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(context.model_dump_json(indent=4))
            
        return self.generate_markdown(json_path)

    def generate_markdown(self, json_path: str) -> str:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        context = WriteupContext(**data)
        
        template = env.get_template("default.md")
        content = template.render(**context.model_dump())
        
        output_path = json_path.replace(".json", ".md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return output_path

    def get_all_writeups(self):
        pattern = os.path.join(self.writeups_dir, "**", "*.json")
        json_files = glob.glob(pattern, recursive=True)
        results = []
        for j_path in sorted(json_files):
            try:
                with open(j_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                md_path = j_path.replace(".json", ".md")
                md_exists = os.path.exists(md_path)
                results.append((data, md_exists))
            except Exception:
                pass
        return results

class TelegraphService:
    def __init__(self):
        self.token_path = os.path.join(os.path.expanduser("~"), ".writeup.env")

    def _get_token(self) -> str:
        if os.path.exists(self.token_path):
            with open(self.token_path, "r") as f:
                for line in f:
                    if line.startswith("TELEGRAPH_TOKEN="):
                        return line.strip().split("=", 1)[1]
        return None

    def _save_token(self, token: str):
        with open(self.token_path, "w") as f:
            f.write(f"TELEGRAPH_TOKEN={token}\\n")
        os.chmod(self.token_path, stat.S_IRUSR | stat.S_IWUSR)

    def auth(self, short_name: str) -> dict:
        tg = Telegraph()
        acc = tg.create_account(short_name=short_name)
        self._save_token(acc['access_token'])
        return acc

    def publish(self, context: WriteupContext) -> str:
        token = self._get_token()
        if token:
            tg = Telegraph(access_token=token)
        else:
            tg = Telegraph()
            acc = tg.create_account(short_name=context.team or "writeup-automatizator")
            self._save_token(acc['access_token'])

        template = env.get_template("default.md")
        md_content = template.render(**context.model_dump())
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        
        html_content = html_content.replace("<h1>", "<h3>").replace("</h1>", "</h3>")
        html_content = html_content.replace("<h2>", "<h4>").replace("</h2>", "</h4>")

        response = tg.create_page(
            context.title,
            html_content=html_content,
            author_name=context.team
        )
        return response['url']
