from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path


class BaseAnalyzer(ABC):
    """分析スロットのベースクラス"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def analyze(
        self,
        pages: List[Dict],
        images_dir: Path,
        ai_client,
        prompt_loader=None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """分析を実行する"""
        raise NotImplementedError

    def create_prompt(self, pages: List[Dict], context: str = "") -> str:
        text_content = ""
        for page in pages[:10]:
            text_content += f"--- ページ {page['page']} ---\n"
            text_content += page.get("text", "") + "\n\n"

        return f"""
{context}

以下の決算書テキストを分析してください。

{text_content}

分析結果は以下の形式で出力してください。
- 分析概要: [具体的な分析概要]
- 重要なポイント: [重要なポイントを箇条書きで]
- 関連ページ: [関連するページ番号]
- 画像候補: [関連する画像のページ番号]
"""

    def find_relevant_images_by_keywords(
        self,
        keywords: List[str],
        pages: List[Dict],
        extra_keywords: List[str] | None = None,
        limit: int = 5,
    ) -> List[int]:
        terms = [kw.lower() for kw in keywords]
        if extra_keywords:
            terms.extend(kw.lower() for kw in extra_keywords)

        relevant_pages: List[int] = []
        for page in pages:
            text = page.get("text", "").lower()
            if any(term in text for term in terms):
                relevant_pages.append(page["page"])
                if len(relevant_pages) >= limit:
                    break
        return relevant_pages

