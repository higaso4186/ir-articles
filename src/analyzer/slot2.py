from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot2Analyzer(BaseAnalyzer):
    """セグメント分析スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="セグメント分析",
            description="事業セグメント別の業績と成長性を評価",
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
        segments = meta.get("segments", [])
        segment_detail = "、".join(segments[:4]) if segments else "セグメント情報が限定的"

        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(2, pages, meta)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            context = (
                f"{company}の主要セグメント（{segment_detail}）について、売上・利益の推移、成長率、利益率、顧客動向を比較分析してください。"
                "セグメント間シナジーやコスト配賦の影響も考慮し、数値を引用しながら記述してください。"
            )
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)

        keywords = ["セグメント", "事業", "売上構成", "business", "segment"]
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

