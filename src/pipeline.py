from __future__ import annotations
from pathlib import Path
import json, time
from dataclasses import dataclass
from schema import PipelineResult, CommonInfo, DocMeta
from pdf_utils import sha256_file, render_pages_to_images, extract_text_per_page, save_jsonl
from extract_common import extract_common
from analyzers import analyze_kpi_summary, analyze_segment_trends, analyze_risk_notes
from md_renderer import render_markdown

@dataclass
class Paths:
    root: Path
    images: Path
    extracted: Path
    outputs: Path
    logs: Path

def ensure_dirs(root: Path) -> Paths:
    paths = Paths(
        root=root,
        images=root / "images",
        extracted=root / "extracted",
        outputs=root / "outputs",
        logs=root / "logs",
    )
    for p in [paths.images, paths.extracted, paths.outputs, paths.logs]:
        p.mkdir(parents=True, exist_ok=True)
    return paths

def run_pipeline(pdf_path: Path, outdir: Path, template_dir: Path) -> PipelineResult:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = ensure_dirs(outdir)
    # Copy source
    (outdir / "source.pdf").write_bytes(pdf_path.read_bytes())

    # Hash and images
    file_hash = sha256_file(pdf_path)
    pages_count = render_pages_to_images(pdf_path, paths.images, dpi=200)

    # Text extraction
    pages = extract_text_per_page(pdf_path)
    save_jsonl(pages, paths.extracted / "pages.jsonl")

    # Common info extraction
    common = extract_common(pages)
    (paths.extracted / "common.json").write_text(common.model_dump_json(indent=2), encoding='utf-8')

    # Analyses
    a1 = analyze_kpi_summary(pages, common)
    a2 = analyze_segment_trends(pages, common)
    a3 = analyze_risk_notes(pages)
    analyses = [a1, a2, a3]
    (paths.extracted / "analyses.json").write_text(
        json.dumps([a.model_dump() for a in analyses], indent=2), encoding='utf-8'
    )

    # Assemble result
    meta = DocMeta(doc_id=file_hash[:12], filename=pdf_path.name, pages=pages_count)
    result = PipelineResult(meta=meta, common=common, analyses=analyses)

    # Render Markdown
    render_markdown(result, template_dir, paths.outputs / "review.md")

    # Log
    runlog = {
        "ts": int(time.time()),
        "file_hash": file_hash,
        "pages": pages_count,
        "outdir": outdir.as_posix()
    }
    (paths.logs / "run.json").write_text(json.dumps(runlog, indent=2), encoding='utf-8')

    return result
