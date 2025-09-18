from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
from analyzer.base import BaseAnalyzer

class Slot3Analyzer(BaseAnalyzer):
    """財務健全性分析スロット"""
    
    def __init__(self):
        super().__init__(
            name="財務健全性",
            description="財務指標とキャッシュフロー分析"
        )
    
    def analyze(self, pages: List[Dict], images_dir: Path, ai_client, prompt_loader=None, company_name: str = "不明企業") -> Dict[str, Any]:
        if prompt_loader:
            prompt = prompt_loader.create_slot_prompt(3, pages, company_name)
            analysis_result = ai_client.generate_analysis(prompt)
        else:
            # フォールバック: プロンプトファイルが読み込めない場合
            print("警告: プロンプトファイルの読み込みに失敗しました。基本分析を実行します。")
            context = "決算資料から財務健全性分析を実行してください。財務比率、キャッシュフロー、財務リスクを分析し、1,500-2,000字で詳細に記述してください。"
            prompt = self.create_prompt(pages, context)
            analysis_result = ai_client.generate_analysis(prompt)
        
        relevant_pages = self.find_relevant_images_by_keywords(
            ["財務", "キャッシュ", "ROE", "ROA", "負債", "借入"], pages
        )
        
        return {
            "title": self.name,
            "content": analysis_result,
            "relevant_pages": relevant_pages,
            "images": [f"images/p{p:03d}.png" for p in relevant_pages[:2]]
        }
    
    def find_relevant_images_by_keywords(self, keywords: List[str], pages: List[Dict]) -> List[int]:
        relevant_pages = []
        for page in pages:
            text = page['text'].lower()
            if any(keyword in text for keyword in keywords):
                relevant_pages.append(page['page'])
        return relevant_pages[:5]
