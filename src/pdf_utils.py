from __future__ import annotations
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
import hashlib
import json

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def render_pages_to_images(pdf_path: Path, images_dir: Path, dpi: int = 200) -> int:
    images_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out = images_dir / f"p{i:03d}.png"
        pix.save(out.as_posix())
    pages = len(doc)
    doc.close()
    return pages

def extract_text_per_page(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text('text') or ''
        pages.append({'page': i, 'text': text})
    doc.close()
    return pages

def save_jsonl(lines: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for obj in lines:
            f.write(json.dumps(obj) + '\n')
