from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from schema import PipelineResult

def render_markdown(result: PipelineResult, template_dir: Path, out_path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(template_dir.as_posix()),
        autoescape=select_autoescape()
    )
    def format_currency(value: int, currency: str | None) -> str:
        if value is None:
            return "N/A"
        prefix = "¥" if currency == "JPY" else ""
        return f"{prefix}{value:,}"
    env.filters['format_currency'] = format_currency

    tpl = env.get_template("review.md.j2")
    md = tpl.render(result=result)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
