\
from __future__ import annotations
from typing import List
import re
from schema import AnalysisItem

def _collect_pages_for_keywords(pages: List[dict], keywords: list[str]) -> list[int]:
    hits = set()
    for p in pages:
        t = p['text']
        for kw in keywords:
            if kw.lower() in t.lower():
                hits.add(p['page'])
    return sorted(hits)

def analyze_kpi_summary(pages: List[dict], common) -> AnalysisItem:
    rev = common.kpis.get('revenue')
    opi = common.kpis.get('operating_income')
    ebt = common.kpis.get('ebitda')

    parts = []
    if rev and rev.value is not None:
        parts.append(f"売上: {rev.value:,}")
    if opi and opi.value is not None:
        parts.append(f"営業利益: {opi.value:,}")
    if ebt and ebt.value is not None:
        parts.append(f"EBITDA: {ebt.value:,}")
    sentence = " / ".join(parts) if parts else "主要KPIの抽出値は未確定です。"

    pages_union = set()
    for k in [rev, opi, ebt]:
        if k:
            pages_union.update(k.page_citations)
    page_list = sorted(pages_union)

    images = [f"images/p{p:03d}.png" for p in page_list]
    return AnalysisItem(
        id="kpi_summary",
        title="KPIサマリ",
        finding=sentence,
        page_citations=page_list,
        images=images
    )

def analyze_segment_trends(pages: List[dict], common) -> AnalysisItem:
    # Look for lines mentioning 'セグメント' and collect most frequent segment-like tokens
    keywords = ['セグメント', 'segment']
    page_list = _collect_pages_for_keywords(pages, keywords)
    # Simple heuristic summary
    seg_names = [s.name for s in (common.segments or [])]
    if seg_names:
        finding = "セグメント出現: " + ", ".join(seg_names[:3])
    else:
        finding = "セグメントに関する明確な記述を検出できませんでした。"
    images = [f"images/p{p:03d}.png" for p in page_list[:2]]
    return AnalysisItem(
        id="segment_trends",
        title="セグメント別トレンド",
        finding=finding,
        page_citations=page_list,
        images=images
    )

def analyze_risk_notes(pages: List[dict]) -> AnalysisItem:
    risk_terms = [
        '為替', '原材料', 'コスト', '需給', '規制', 'リスク', '不確実性',
        '災害', 'サプライチェーン', '金利', 'インフレ', '地政学', '競争'
    ]
    sentences = []
    cites = set()
    for p in pages:
        for sent in re.split(r"[。．.]\s*", p['text']):
            if any(term in sent for term in risk_terms):
                s = sent.strip()
                if s and len(s) > 8:
                    sentences.append("・" + s + "。")
                    cites.add(p['page'])
    if not sentences:
        sentences.append("・リスクに関する明確な文章を検出できませんでした。")
    images = [f"images/p{p:03d}.png" for p in sorted(cites)[:2]]
    return AnalysisItem(
        id="risk_notes",
        title="リスク・注記",
        finding="\n".join(sentences[:5]),
        page_citations=sorted(cites),
        images=images
    )
