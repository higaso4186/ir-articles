from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot1Analyzer(BaseAnalyzer):
    """業績分析スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="業績分析",
            description="売上・利益のYoY/QoQ/計画差異と主要ドライバーを精査",
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
                f"{company}（業界: {industry}、期間: {period}）の決算資料を基に、売上・利益および主要KPIのYoY・QoQ・計画差異を差額と比率で整理してください。"
                f"主要KPI: {kpi_summary}。価格/数量/ミックス/コスト要因でマージンブリッジを組み立て、固定費・変動費・一過性費用を切り分けてください。"
                "トップ3ドライバーの寄与金額と寄与率を算出し、根拠ページを( Pxx )形式で必ず引用してください。持続性や逆風要因も定量指標とともに整理してください。"
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


