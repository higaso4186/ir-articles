from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot1Analyzer(BaseAnalyzer):
    """業績分析スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="業績分析",
            description="売上・利益の推移と主要ドライバーを分析",
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
        period = meta.get("period_label") or meta.get("fiscal_year") or "対象期間不明"
        kpi_summary = meta.get("kpi_summary") or "主要KPI情報が取得できていません"

        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(1, pages, meta)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            context = (
                f"{company}（業界: {industry}、期間: {period}）の決算資料から、売上・利益の推移と変動要因を特定してください。"
                f"主要KPI: {kpi_summary}。前年同期比や会社計画との差異が分かる場合は数値とともに示してください。"
            )
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)

        relevant_pages = self.find_relevant_images_by_keywords(
            ["売上", "利益", "収益", "業績", "前年", "増減"],
            pages,
            extra_keywords=meta.get("metric_keywords"),
        )

        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]],
        }

