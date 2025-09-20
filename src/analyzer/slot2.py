from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot2Analyzer(BaseAnalyzer):
    """セグメント分析スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="セグメント分析",
            description="セグメント別の差異分析と戦略連動を精査",
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
                f"{company}の主要セグメント（{segment_detail}）について、売上高・営業利益・利益率・構成比のYoY/QoQ/計画差異を差額と比率で比較し、主因を定量的に整理してください。"
                "顧客KPIやチャネル/地域別の動向を示し、共通費配賦やシナジー/カニバリの影響をページ番号付きで解説してください。"
                "戦略KPIやマイルストンとの連動度を明示し、成長セグメントと停滞セグメントそれぞれの打ち手とリスク/機会を整理してください。"
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


