from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot4Analyzer(BaseAnalyzer):
    """戦略・展望スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="戦略・展望",
            description="戦略KPIと資本配分・競争優位を多面的に評価",
        )

    def analyze(
        self,
        pages: List[Dict],
        images_dir: Path,
        ai_client,
        prompt_loader=None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        meta = metadata or {}
        company = meta.get("company_name", "不明企業")
        industry = meta.get("industry", "業界不明")
        segments = meta.get("segments", [])
        segment_text = "、".join(segments[:4]) if segments else "セグメント情報が限定的"

        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(4, pages, meta)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            context = (
                f"{company}（業界: {industry}）の中期戦略と重点施策を、戦略テーマ×KGI/KPI、達成タイムライン、進捗度で整理してください。"
                f"主要セグメント: {segment_text}。Capex/M&A/R&D/人材投資の規模と回収指標、ESG施策、マイルストン、カタリストをページ番号付きで解説してください。"
                "市場シェア・競合比較・シナリオ別アウトルックを定量化し、成功/失敗の分岐要因とモニタリング指標を提示してください。"
            )
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)

        keywords = ["戦略", "施策", "成長", "中期計画", "展望", "重点"]
        relevant_pages = self.find_relevant_images_by_keywords(
            keywords,
            pages,
            extra_keywords=meta.get("segment_keywords"),
        )

        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]],
        }


