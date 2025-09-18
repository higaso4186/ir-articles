from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot3Analyzer(BaseAnalyzer):
    """財務健全性スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="財務健全性",
            description="資本構成とキャッシュフローの健全性を検証",
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
        period = meta.get("period_label") or meta.get("fiscal_year") or "対象期間不明"

        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(3, pages, meta)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            context = (
                f"{company}（期間: {period}）の財務健全性を、流動性・自己資本比率・キャッシュフロー創出力の観点で分析してください。"
                "有利子負債の推移、財務レバレッジ、配当・投資方針にも触れ、関連ページと数値を引用してください。"
            )
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)

        keywords = ["自己資本", "キャッシュフロー", "負債", "財務", "資本", "財政状態"]
        relevant_pages = self.find_relevant_images_by_keywords(keywords, pages)

        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]],
        }

