from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
import json

class BaseAnalyzer(ABC):
    """分析項目のベースクラス"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def analyze(self, pages: List[Dict], images_dir: Path, ai_client) -> Dict[str, Any]:
        """
        分析を実行する
        
        Args:
            pages: ページ別テキストデータ
            images_dir: 画像ディレクトリのパス
            ai_client: AI APIクライアント
            
        Returns:
            分析結果の辞書
        """
        pass
    
    def create_prompt(self, pages: List[Dict], context: str = "") -> str:
        """AI用のプロンプトを作成"""
        # 全ページのテキストを結合（最初の10ページまで）
        text_content = ""
        for page in pages[:10]:
            text_content += f"--- ページ {page['page']} ---\n"
            text_content += page['text'] + "\n\n"
        
        return f"""
{context}

以下の決算資料のテキストを分析してください：

{text_content}

分析結果は以下の形式で出力してください：
- 分析内容: [具体的な分析内容]
- 重要なポイント: [重要なポイントを箇条書きで]
- 関連ページ: [関連するページ番号]
- 画像候補: [関連する画像のページ番号]
"""
    
    def find_relevant_images(self, analysis_result: str, pages: List[Dict]) -> List[int]:
        """分析結果に基づいて関連する画像ページを特定"""
        # 簡単な実装：分析結果に含まれるページ番号を抽出
        import re
        page_numbers = re.findall(r'ページ\s*(\d+)', analysis_result)
        return [int(p) for p in page_numbers if int(p) <= len(pages)]
