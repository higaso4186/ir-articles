from __future__ import annotations
from pathlib import Path
import json, time
from dataclasses import dataclass
from pdf_utils import sha256_file, render_pages_to_images, extract_text_per_page, save_jsonl
from ai_client import get_ai_client
from prompt_loader import PromptLoader
from analyzer.slot1 import Slot1Analyzer
from analyzer.slot2 import Slot2Analyzer
from analyzer.slot3 import Slot3Analyzer
from analyzer.slot4 import Slot4Analyzer
from analyzer.slot5 import Slot5Analyzer
from image_matcher import ImageMatcher

@dataclass
class Paths:
    root: Path
    images: Path
    extracted: Path
    outputs: Path
    logs: Path

def extract_company_name(pages: list) -> str:
    """PDFから会社名を抽出"""
    import re
    
    # 最初の数ページから会社名を抽出
    for page in pages[:5]:  # 最初の5ページをチェック
        text = page.get('text', '')
        
        # 一般的な会社名パターンを検索
        patterns = [
            r'([^。\n]+株式会社)',
            r'([^。\n]+有限会社)',
            r'([^。\n]+合資会社)',
            r'([^。\n]+合名会社)',
            r'([^。\n]+Inc\.)',
            r'([^。\n]+Corp\.)',
            r'([^。\n]+Ltd\.)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 最も長いマッチを選択（より具体的な会社名）
                company_name = max(matches, key=len).strip()
                if len(company_name) > 3:  # 最低限の長さをチェック
                    print(f"抽出された会社名: {company_name}")
                    return company_name
    
    # 抽出できない場合はデフォルト
    print("警告: 会社名を抽出できませんでした。デフォルト名を使用します。")
    return "不明企業"

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

def run_enhanced_pipeline(pdf_path: Path, outdir: Path, ai_provider: str = "openai") -> dict:
    """高品質な記事生成パイプラインを実行（5倍の品質向上版）"""
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
    
    # AI クライアントとプロンプトローダーを初期化
    ai_client = get_ai_client(ai_provider)
    prompt_loader = PromptLoader()
    
    # 会社名を抽出
    company_name = extract_company_name(pages)
    
    # 1. 概要・冒頭部分を生成
    print("概要部分を生成中...")
    overview_prompt = prompt_loader.create_overview_prompt(pages, company_name)
    overview_content = ai_client.generate_article(overview_prompt)
    
    # 2. 各スロットで詳細分析を実行
    analyzers = [
        Slot1Analyzer(),  # 業績分析
        Slot2Analyzer(),  # セグメント分析
        Slot3Analyzer(),  # 財務健全性
        Slot4Analyzer(),  # 戦略・展望
        Slot5Analyzer()   # リスク要因
    ]
    
    slot_results = []
    for i, analyzer in enumerate(analyzers, 1):
        print(f"スロット{i}（{analyzer.name}）を分析中...")
        try:
            result = analyzer.analyze(pages, paths.images, ai_client, prompt_loader, company_name)
            slot_results.append(result)
        except Exception as e:
            print(f"スロット{i}でエラー: {str(e)}")
            # エラーが発生した場合は空の結果を追加
            slot_results.append({
                "title": analyzer.name,
                "content": f"分析エラー: {str(e)}",
                "relevant_pages": [],
                "images": []
            })
    
    # 3. 投資判断・まとめ部分を生成
    print("投資判断を生成中...")
    investment_prompt_template = prompt_loader.load_prompt("投資判断生成.md")
    
    # 分析結果をまとめて投資判断プロンプトに追加
    analysis_summary = ""
    for result in slot_results:
        analysis_summary += f"### {result['title']}\n{result['content']}\n\n"
    
    investment_prompt = f"""
{investment_prompt_template}

## 分析対象企業情報
**企業名**: {company_name}
**決算期**: 2026年5月期第1四半期

## 各分析結果
{analysis_summary}

上記の分析結果を総合して、具体的で実用的な投資判断を作成してください。
特にターゲット価格は複数の評価手法を用いて算出し、投資タイミングを明確に示してください。
"""
    investment_content = ai_client.generate_article(investment_prompt)
    
    # 4. 最終記事を組み立て
    print("最終記事を組み立て中...")
    
    # 各スロットの内容を結合
    analysis_sections = []
    all_images = []
    
    for result in slot_results:
        analysis_sections.append(f"## {result['title']}\n\n{result['content']}\n")
        if result['images']:
            for img in result['images']:
                analysis_sections.append(f"![{result['title']}]({img})\n")
        all_images.extend(result['relevant_pages'])
    
    # 最終記事の構成
    final_article = f"""{overview_content}

{chr(10).join(analysis_sections)}

{investment_content}

---

**▼新着記事をTwitterでお届けします。**
・Twitter: https://twitter.com/corp_analysis_lab

気に入ってくださった方は、↓から「スキ」「フォロー」してください！
"""
    
    # 5. 結果を保存
    total_word_count = len(final_article.split())
    
    result = {
        "company_name": company_name,
        "filename": pdf_path.name,
        "doc_id": file_hash[:12],
        "pages": pages_count,
        "article": {
            "content": final_article,
            "word_count": total_word_count,
            "overview": overview_content,
            "slot_results": slot_results,
            "investment_judgment": investment_content,
            "total_images": len(set(all_images))
        }
    }
    
    # 中間結果を保存
    (paths.extracted / "overview.json").write_text(
        json.dumps({"content": overview_content}, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (paths.extracted / "slot_results.json").write_text(
        json.dumps(slot_results, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (paths.extracted / "investment.json").write_text(
        json.dumps({"content": investment_content}, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (paths.extracted / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    
    # 最終記事をMarkdownファイルとして保存
    (paths.outputs / "article.md").write_text(final_article, encoding="utf-8")
    
    # Log
    runlog = {
        "ts": int(time.time()),
        "file_hash": file_hash,
        "pages": pages_count,
        "outdir": outdir.as_posix(),
        "ai_provider": ai_provider,
        "word_count": total_word_count,
        "images_used": len(set(all_images)),
        "slots_processed": len(slot_results)
    }
    (paths.logs / "run.json").write_text(json.dumps(runlog, indent=2, ensure_ascii=False), encoding='utf-8')
    
    return result
