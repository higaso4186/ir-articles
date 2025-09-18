from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot4Analyzer(BaseAnalyzer):
    """戦略・展望スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="戦略・展望",
            description="経営戦略と成長シナリオを評価",
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
                f"{company}（業界: {industry}）の経営戦略と中期計画を整理し、競争優位性と実現可能性を評価してください。"
                f"主要セグメント: {segment_text}。投資計画、技術開発、サステナビリティ施策などのアクションと成果指標を紐付けて分析してください。"
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

