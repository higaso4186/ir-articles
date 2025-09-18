from __future__ import annotations
import argparse
from pathlib import Path
from enhanced_pipeline import run_enhanced_pipeline


def parse_args():
    ap = argparse.ArgumentParser(description="Enhanced AI-powered IR PDF -> Article pipeline")
    ap.add_argument("--pdf", required=True, help="Path to input PDF")
    ap.add_argument("--outdir", required=True, help="Output directory (will be created)")
    ap.add_argument("--ai-provider", default="openai", choices=["mock", "openai"],
                    help="AI provider (default: openai)")
    return ap.parse_args()


def main():
    args = parse_args()
    pdf = Path(args.pdf).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    if not pdf.exists():
        raise FileNotFoundError(pdf)

    res = run_enhanced_pipeline(pdf, outdir, args.ai_provider)
    print(f"Done. doc_id={res['doc_id']}, pages={res['pages']}")
    print(f"Article: {outdir}/outputs/article.md")
    print(f"Character count: {res['article']['character_count']}")
    print(f"Approx. word count: {res['article']['word_count']}")
    print(f"Images used: {res['article']['total_images']}")


if __name__ == "__main__":
    main()
