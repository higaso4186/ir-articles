from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
from ai_client import get_ai_client

class SummaryGenerator:
    """サマリー生成クラス"""
    
    def __init__(self, ai_provider: str = "mock"):
        self.ai_client = get_ai_client(ai_provider)
    
    def generate_summary(self, pages: List[Dict], format_template: str) -> Dict[str, Any]:
        """フォーマットテンプレートに基づいてサマリーを生成"""
        
        # 全ページのテキストを結合（最初の15ページまで）
        text_content = ""
        for page in pages[:15]:
            text_content += f"--- ページ {page['page']} ---\n"
            text_content += page['text'] + "\n\n"
        
        prompt = f"""
あなたは決算分析の専門家です。以下の決算資料を分析し、指定されたフォーマットに従ってサマリーを作成してください。

【フォーマットテンプレート】
{format_template}

【決算資料のテキスト】
{text_content}

上記のフォーマットに従って、決算の要点を簡潔にまとめてください。
各項目について具体的な数値や事実を含めて記述してください。
"""
        
        summary_result = self.ai_client.generate_summary(prompt)
        
        return {
            "content": summary_result,
            "format_used": format_template
        }
