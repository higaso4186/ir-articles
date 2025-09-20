from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from analyzer.base import BaseAnalyzer


class Slot3Analyzer(BaseAnalyzer):
    """財務健全性スロット"""

    def __init__(self) -> None:
        super().__init__(
            name="財務健全性",
            description="資本構成・流動性・資本政策を多角的に検証",
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
                f"{company}（期間: {period}）の財務健全性を、自己資本比率・ネットD/E・流動性指標・ネットデット/EBITDA・インタレストカバレッジ・手元流動性日数まで網羅して分析してください。"
                "運転資本回転日数のYoY/QoQ比較、営業/投資/財務CFのブリッジ、フリーCFの持続性、借入金満期プロファイルとコベナンツ、配当/自己株/投資方針の整合を定量的に整理してください。"
                "リスクシナリオ別の耐性とモニタリングすべき指標を提示し、全ての主要指標にページ番号を( Pxx )形式で付記してください。"
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


