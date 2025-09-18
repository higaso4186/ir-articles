from __future__ import annotations
import argparse
from pathlib import Path
from pipeline import run_pipeline

def parse_args():
    ap = argparse.ArgumentParser(description="IR PDF -> Markdown pipeline")
    ap.add_argument("--pdf", required=True, help="Path to input PDF")
    ap.add_argument("--outdir", required=True, help="Output directory (will be created)")
    ap.add_argument("--templates", default=str(Path(__file__).parent.parent / "templates"),
                    help="Template directory (default: ./templates)")
    return ap.parse_args()

def main():
    args = parse_args()
    pdf = Path(args.pdf).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    tpl = Path(args.templates).expanduser().resolve()
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    res = run_pipeline(pdf, outdir, tpl)
    print(f"Done. doc_id={res.meta.doc_id}, pages={res.meta.pages}")
    print(f"Output: {outdir}/outputs/review.md")

if __name__ == "__main__":
    main()
