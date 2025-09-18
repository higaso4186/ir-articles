from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot5Analyzer(BaseAnalyzer):
    """リスク要因スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="リスク・注記",
            description="事業・財務リスクと開示姿勢を整理",
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

        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(5, pages, meta)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            context = (
                f"{company}（業界: {industry}）の主要リスクを、マクロ環境・競争・オペレーション・法規制の観点で整理してください。"
                "決算書からの引用箇所を示し、影響度・発生可能性・緩和策を明確に記述してください。"
            )
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)

        keywords = [
            "リスク",
            "為替",
            "原材料",
            "需給",
            "コスト",
            "規制",
            "法令",
            "不確実性",
            "サプライ",
            "災害",
            "競争",
        ]
        relevant_pages = self.find_relevant_images_by_keywords(keywords, pages)

        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]],
        }

