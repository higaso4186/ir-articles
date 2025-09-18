from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
from analyzer.base import BaseAnalyzer

class Slot1Analyzer(BaseAnalyzer):
    """業績分析スロット"""
    
    def __init__(self):
        super().__init__(
            name="業績分析",
            description="売上・利益の推移と要因分析"
        )
    
    def analyze(self, pages: List[Dict], images_dir: Path, ai_client, prompt_loader=None, company_name: str = "不明企業") -> Dict[str, Any]:
        if prompt_loader:
            # 専用プロンプトを使用
            prompt = prompt_loader.create_slot_prompt(1, pages, company_name)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            # フォールバック: プロンプトファイルが読み込めない場合
            print("警告: プロンプトファイルの読み込みに失敗しました。基本分析を実行します。")
            context = "決算資料から業績分析を実行してください。売上高、営業利益、純利益の推移と要因を分析し、1,500-2,000字で詳細に記述してください。"
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)
        
        # 関連画像を特定（業績関連のキーワード）
        relevant_pages = self.find_relevant_images_by_keywords(
            ["売上", "利益", "収益", "業績", "前年", "増減"], pages
        )
        
        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]]
        }
    
    def find_relevant_images_by_keywords(self, keywords: List[str], pages: List[Dict]) -> List[int]:
        """キーワードベースで関連画像を特定"""
        relevant_pages = []
        for page in pages:
            text = page['text'].lower()
            if any(keyword in text for keyword in keywords):
                relevant_pages.append(page['page'])
        return relevant_pages[:5]  # 最大5ページまで
