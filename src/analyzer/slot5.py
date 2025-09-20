from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot5Analyzer(BaseAnalyzer):
    """リスク要因スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="リスク・注記",
            description="リスクスコアとモニタリング計画を体系化",
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
                f"{company}（業界: {industry}）の主要リスクを、マクロ・競争・オペレーション・法規制/コンプラ・財務の5分類で整理し、発生可能性・影響度・残存リスクをスコアリングしてください。"
                "各リスクの緩和策と進捗、モニタリング指標・責任部門・頻度、外部環境/規制動向の感応度、BCP・サイバー対策・内部統制との関連をページ番号付きで解説してください。"
                "トリガーイベントごとの対応フローと投資家が注視すべきチェックポイントを提示してください。"
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


