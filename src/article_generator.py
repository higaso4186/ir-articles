from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
from ai_client import get_ai_client
from prompt_loader import PromptLoader

class ArticleGenerator:
    """高品質な決算分析記事を生成するクラス"""
    
    def __init__(self, ai_provider: str = "openai"):
        self.ai_client = get_ai_client(ai_provider)
        self.prompt_loader = PromptLoader()
    
    def generate_article(self, pages: List[Dict], company_name: str = "不明企業") -> Dict[str, Any]:
        """決算分析記事を生成"""
        
        # プロンプトを作成
        prompt = self.prompt_loader.create_article_prompt(pages, company_name)
        
        # AIで記事を生成
        article_content = self.ai_client.generate_article(prompt)
        
        return {
            "content": article_content,
            "company_name": company_name,
            "word_count": len(article_content.split()),
            "prompt_used": "決算書分析記事作成プロンプト"
        }
