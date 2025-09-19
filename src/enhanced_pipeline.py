from __future__ import annotations
from pathlib import Path
import copy
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pdf_utils import sha256_file, render_pages_to_images, extract_text_per_page, save_jsonl
from ai_client import get_ai_client
from prompt_loader import PromptLoader
from analyzer.slot1 import Slot1Analyzer
from analyzer.slot2 import Slot2Analyzer
from analyzer.slot3 import Slot3Analyzer
from analyzer.slot4 import Slot4Analyzer
from analyzer.slot5 import Slot5Analyzer
from extract_common import extract_common
from schema import CommonInfo


@dataclass
class Paths:
    root: Path
    images: Path
    extracted: Path
    outputs: Path
    logs: Path


INDUSTRY_PATTERNS: List[tuple[str, List[str]]] = [
    ("テクノロジー", ["saas", "クラウド", "itサービス", "ソフトウェア", "プラットフォーム", "dx"]),
    ("小売・EC", ["小売", "ec", "通販", "店舗", "eコマース", "チャネル"]),
    ("製造", ["製造", "生産", "工場", "ものづくり"]),
    ("物流・インフラ", ["物流", "配送", "倉庫", "インフラ", "供給網"]),
    ("金融", ["金融", "銀行", "証券", "保険", "資産運用"]),
    ("不動産", ["不動産", "賃貸", "物件", "開発"]),
    ("医療・ヘルスケア", ["医療", "ヘルスケア", "製薬", "バイオ", "臨床"]),
    ("エネルギー", ["エネルギー", "発電", "電力", "ガス", "再生可能"]),
]

UNIT_LABEL = {
    "million": "百",  # 百万円・百万ドル等
    "thousand": "千",
    "one": ""
}

CURRENCY_SYMBOL = {
    "JPY": "¥",
    "USD": "$",
}


def extract_company_name(pages: list) -> str:
    """PDFから会社名を抽出"""
    import re

    for page in pages[:5]:
        text = page.get("text", "")
        patterns = [
            r"([^、En]+株式会社)",
            r"([^、En]+有限会社)",
            r"([^、En]+合資会社)",
            r"([^、En]+合名会社)",
            r"([^、En]+Inc\.)",
            r"([^、En]+Corp\.)",
            r"([^、En]+Ltd\.)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                company_name = max(matches, key=len).strip()
                company_name = company_name.splitlines()[-1].strip()
                company_name = re.sub(r'^(?:[0-9０-９]{4})年\s*\d{1,2}月\s*\d{1,2}日\s*', '', company_name)
                if len(company_name) > 3:
                    print(f"抽出された会社名: {company_name}")
                    return company_name

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


def infer_industry(common: CommonInfo, pages: List[dict]) -> str:
    segment_names = [seg.name for seg in (common.segments or [])]
    searchable_text = "\n".join(page.get("text", "") for page in pages[:6]).lower()

    for label, keywords in INDUSTRY_PATTERNS:
        lowered = [kw.lower() for kw in keywords]
        if any(keyword in searchable_text for keyword in lowered):
            return label
        if any(keyword in seg.lower() for seg in segment_names for keyword in lowered):
            return label
    return "業界不明"


def format_amount(value: int | None, common: CommonInfo) -> str:
    if value is None:
        return "数値未取得"
    unit = common.unit or "one"
    symbol = CURRENCY_SYMBOL.get(common.currency or "", "")
    divisor = 1
    if unit == "million":
        divisor = 1_000_000
    elif unit == "thousand":
        divisor = 1_000

    display_value = value / divisor if divisor != 1 else value
    if isinstance(display_value, float) and not display_value.is_integer():
        formatted = f"{display_value:,.2f}"
    else:
        formatted = f"{int(display_value):,}"
    unit_label = UNIT_LABEL.get(unit, "")
    currency_suffix = "円" if (common.currency or "").upper() == "JPY" else ""
    return f"{symbol}{formatted}{unit_label}{currency_suffix}"


def build_kpi_summary(common: CommonInfo) -> str:
    label_map = {
        "revenue": "売上高",
        "operating_income": "営業利益",
        "ebitda": "EBITDA",
    }
    fragments = []
    for key, label in label_map.items():
        kpi = common.kpis.get(key)
        if kpi and kpi.value is not None:
            fragments.append(f"{label}: {format_amount(kpi.value, common)}")
    return " / ".join(fragments)


def build_segment_highlights(common: CommonInfo) -> List[str]:
    highlights = []
    for seg in common.segments or []:
        amount = format_amount(seg.revenue, common) if seg.revenue is not None else "数値未取得"
        highlights.append(f"{seg.name}: {amount}")
    return highlights


def build_slot_guidance(metadata: Dict[str, Any]) -> Dict[int, str]:
    company = metadata.get("company_name", "対象企業")
    industry = metadata.get("industry", "業界不明")
    period = metadata.get("period_label") or metadata.get("fiscal_year") or "最新決算"
    kpi_summary = metadata.get("kpi_summary") or "主要KPI情報は限定的です。"
    segments = metadata.get("segments", [])
    segment_text = "、".join(segments[:4]) if segments else "セグメント情報が限定的"
    segment_details = metadata.get("segment_descriptions", [])
    segment_detail_text = " / ".join(segment_details[:4]) if segment_details else segment_text

    guidance: Dict[int, str] = {}
    guidance[1] = (
        f"{company}（業界: {industry}、期間: {period}）の業績を、売上・利益の変動要因、前年同期比、計画との差異の観点で詳細に評価してください。"
        f"主要KPI: {kpi_summary}。数値を引用し、セグメント間の寄与度や一過性要因があれば必ず触れてください。"
    )
    guidance[2] = (
        f"事業セグメント構成: {segment_detail_text}。各セグメントの成長率・利益率・顧客動向を比較し、資源配分の妥当性や重点施策を明示してください。"
        "共通費配賦やセグメント間シナジーにも言及し、定量的指標があれば引用してください。"
    )
    guidance[3] = (
        "財務健全性を流動性、自己資本比率、キャッシュフロー創出力の観点で分析し、債務返済能力や投資余力を評価してください。"
        "BS・PL・CFの該当箇所から数値を引用し、レバレッジ指標や資金繰り上のリスクも整理してください。"
    )
    guidance[4] = (
        f"{industry}業界の競争環境を踏まえ、経営戦略・成長戦略・中期計画の実現可能性を検証してください。"
        f"主要セグメント: {segment_text}。技術投資、M&A、サステナビリティ対応などの取り組みと、その成果指標を紐付けて解説してください。"
    )
    guidance[5] = (
        "マクロ・競争・オペレーショナル・法規制の各リスクを網羅し、決算資料内の記載と外部環境の示唆を統合してください。"
        "発生可能性と影響度を明示し、緩和策や残存リスクを定量的に示せる箇所があれば引用してください。"
    )
    return guidance


def build_metadata(common: CommonInfo, pages: List[dict], company_name: str) -> Dict[str, Any]:
    industry = infer_industry(common, pages)
    kpi_summary = build_kpi_summary(common)
    segments = [seg.name for seg in (common.segments or [])]
    segment_descriptions = build_segment_highlights(common)

    metadata: Dict[str, Any] = {
        "company_name": company_name,
        "industry": industry,
        "period_label": common.period_label,
        "fiscal_year": common.fiscal_year,
        "accounting_standard": common.accounting_standard,
        "currency": common.currency,
        "unit": common.unit,
        "kpi_summary": kpi_summary,
        "segments": segments,
        "segment_descriptions": segment_descriptions,
    }
    metadata["metric_keywords"] = [label for label in ["売上高", "営業利益", "営業利益率", "EBITDA", "経常利益"] if label]
    metadata["segment_keywords"] = segments
    metadata["overview_guidance"] = (
        f"{company_name}（業界: {industry}、期間: {common.period_label or common.fiscal_year or '期間情報不明'}）の決算概要を、主要トピック3〜4項目に整理してください。"
        f"可能な限り数値と引用ページを併記し、{kpi_summary or '主要KPI情報が取得できていません。'}を踏まえたトーンで記述してください。"
    )
    metadata["investment_guidance"] = (
        f"業界: {industry}、期間: {common.period_label or common.fiscal_year or '期間情報不明'}。"
        "バリュエーションやリスク・リターンのバランスを定量・定性両面から評価し、投資判断を明確に提示してください。"
    )
    metadata["slot_guidance"] = build_slot_guidance(metadata)
    return metadata


def count_characters(text: str) -> int:
    return sum(1 for ch in text if not ch.isspace())


def summarize_usage(usage: Optional[Dict[str, Any]]) -> Dict[str, int]:
    tokens = {'input': 0, 'cached_input': 0, 'output': 0, 'total': 0}
    if not usage:
        return tokens
    if isinstance(usage, dict):
        for key, target in (('prompt_tokens', 'input'), ('completion_tokens', 'output'), ('total_tokens', 'total')):
            value = usage.get(key)
            if isinstance(value, int):
                tokens[target] = value
        details = usage.get('prompt_tokens_details')
        if isinstance(details, dict):
            cached = details.get('cached_tokens')
            if isinstance(cached, int):
                tokens['cached_input'] = cached
    return tokens


def run_enhanced_pipeline(pdf_path: Path, outdir: Path, ai_provider: str = "openai") -> dict:
    """高品質な記事生成パイプラインを実行"""
    outdir.mkdir(parents=True, exist_ok=True)
    paths = ensure_dirs(outdir)

    (outdir / "source.pdf").write_bytes(pdf_path.read_bytes())

    file_hash = sha256_file(pdf_path)
    pages_count = render_pages_to_images(pdf_path, paths.images, dpi=200)

    pages = extract_text_per_page(pdf_path)
    save_jsonl(pages, paths.extracted / "pages.jsonl")

    common = extract_common(pages)
    (paths.extracted / "common.json").write_text(
        common.model_dump_json(indent=2), encoding="utf-8"
    )

    ai_client = get_ai_client(ai_provider)
    prompt_loader = PromptLoader()
    cost_records: List[Dict[str, Any]] = []

    company_name = extract_company_name(pages)
    metadata = build_metadata(common, pages, company_name)
    metadata_prompt_versions = metadata.setdefault("prompt_versions", {})

    def record_usage(step: str, prompt_file: Optional[str]) -> Dict[str, Any]:
        usage_snapshot = ai_client.last_usage if isinstance(ai_client.last_usage, dict) else None
        tokens = summarize_usage(usage_snapshot)
        entry: Dict[str, Any] = {"step": step, "model": getattr(ai_client, "model_name", None), "tokens": tokens}
        if prompt_file:
            version = prompt_loader.get_prompt_version(prompt_file)
            entry["prompt_file"] = prompt_file
            entry["prompt_version"] = version
            metadata_prompt_versions[step] = version
        cost_records.append(entry)
        return entry

    print("概要セクションを生成中...")
    overview_prompt = prompt_loader.create_overview_prompt(pages, metadata)
    overview_content = ai_client.generate_article(overview_prompt)
    record_usage("overview", "概要生成.md")

    analyzers = [
        Slot1Analyzer(),
        Slot2Analyzer(),
        Slot3Analyzer(),
        Slot4Analyzer(),
        Slot5Analyzer(),
    ]

    slot_results: List[Dict[str, Any]] = []
    for i, analyzer in enumerate(analyzers, 1):
        slot_file = prompt_loader.get_slot_filename(i)
        print(f"Analyzing slot {i} ({analyzer.name})...")
        try:
            result = analyzer.analyze(pages, paths.images, ai_client, prompt_loader, metadata)
        except Exception as exc:  # noqa: BLE001
            print(f"Slot {i} raised an error: {exc}")
            result = {
                "title": analyzer.name,
                "content": f"���̓G���[: {exc}",
                "relevant_pages": [],
                "images": [],
            }
        entry = record_usage(f"slot{i}", slot_file)
        result["prompt_file"] = slot_file
        result["prompt_version"] = entry.get("prompt_version")
        slot_results.append(result)


    print("Generating investment section...")
    investment_prompt_file = "投資判断生成.md"
    investment_prompt_template = prompt_loader.load_prompt(investment_prompt_file)
    analysis_summary = ""
    for result in slot_results:
        analysis_summary += f"### {result['title']}\n{result['content']}\n\n"

    industry = metadata.get("industry", "業界不明")
    period_label = metadata.get("period_label") or metadata.get("fiscal_year") or "期間情報不明"
    segment_block = ", ".join(metadata.get("segments", [])[:5]) or "セグメント情報が取得できていません"
    kpi_summary = metadata.get("kpi_summary") or "主要KPI情報が取得できていません"

    investment_prompt = f"""
{investment_prompt_template}

## 企業プロファイル
- 企業名: {company_name}
- 業界: {industry}
- 会計期間: {period_label}
- 主要KPI: {kpi_summary}
- 主なセグメント: {segment_block}

## 分析結果の要約
{analysis_summary}

{metadata.get('investment_guidance', '')}
"""
    investment_content = ai_client.generate_article(investment_prompt)
    record_usage("investment", investment_prompt_file)

    print("最終記事を整形中...")
    analysis_sections: List[str] = []
    all_images: List[int] = []

    for result in slot_results:
        analysis_sections.append(f"## {result['title']}\n\n{result['content']}\n")
        if result["images"]:
            for img in result["images"]:
                analysis_sections.append(f"![{result['title']}]({img})\n")
        all_images.extend(result["relevant_pages"])

    final_article = f"""{overview_content}

{chr(10).join(analysis_sections)}

{investment_content}

---

**▼新着記事をTwitterでお届けします**
・Twitter: https://twitter.com/corp_analysis_lab

気に入ってくださった方は、noteから「スキ」「フォロー」をお願いします。
"""

    total_word_count = len(final_article.split())
    total_character_count = count_characters(final_article)

    totals = {'input': 0, 'cached_input': 0, 'output': 0, 'total': 0}
    for record in cost_records:
        for key in totals:
            value = record['tokens'].get(key) if isinstance(record.get('tokens'), dict) else None
            if isinstance(value, int):
                totals[key] += value

    cost_summary = {
        'model': getattr(ai_client, 'model_name', None),
        'calls': cost_records,
        'totals': totals,
    }

    result = {
        "company_name": company_name,
        "filename": pdf_path.name,
        "doc_id": file_hash[:12],
        "pages": pages_count,
        "common": common.model_dump(),
        "metadata": metadata,
        "article": {
            "content": final_article,
            "word_count": total_word_count,
            "character_count": total_character_count,
            "overview": overview_content,
            "slot_results": slot_results,
            "investment_judgment": investment_content,
            "total_images": len(set(all_images)),
            "token_usage": cost_summary,
        },
    }

    (paths.extracted / "overview.json").write_text(
        json.dumps({"content": overview_content}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (paths.extracted / "slot_results.json").write_text(
        json.dumps(slot_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (paths.extracted / "investment.json").write_text(
        json.dumps({"content": investment_content}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (paths.extracted / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (paths.extracted / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    (paths.outputs / "article.md").write_text(final_article, encoding="utf-8")
    (paths.outputs / "cost.json").write_text(
        json.dumps(cost_summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    runlog = {
        "ts": int(time.time()),
        "file_hash": file_hash,
        "pages": pages_count,
        "outdir": outdir.as_posix(),
        "ai_provider": ai_provider,
        "word_count": total_word_count,
        "character_count": total_character_count,
        "industry": metadata.get("industry"),
        "images_used": len(set(all_images)),
        "slots_processed": len(slot_results),
        "tokens": totals,
    }
    (paths.logs / "run.json").write_text(json.dumps(runlog, indent=2, ensure_ascii=False), encoding="utf-8")

    return result


