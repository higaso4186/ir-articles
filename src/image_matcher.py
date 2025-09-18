from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import re

class ImageMatcher:
    """記事内容に基づいて適切な画像を選択・埋め込みするクラス"""
    
    def __init__(self, images_dir: Path):
        self.images_dir = images_dir
    
    def find_relevant_images(self, article_content: str, pages: List[Dict]) -> List[Dict[str, Any]]:
        """記事内容に基づいて関連する画像を特定"""
        
        # キーワードベースの画像選択
        keyword_mappings = {
            "売上": ["売上", "収益", "revenue", "sales"],
            "利益": ["利益", "profit", "income", "営業利益"],
            "セグメント": ["セグメント", "segment", "事業", "business"],
            "財務": ["財務", "financial", "キャッシュ", "cash"],
            "戦略": ["戦略", "strategy", "計画", "plan"],
            "リスク": ["リスク", "risk", "課題", "challenge"],
            "投資": ["投資", "investment", "資本", "capital"],
            "成長": ["成長", "growth", "拡大", "expansion"]
        }
        
        # 記事内容からキーワードを抽出
        found_keywords = []
        for category, keywords in keyword_mappings.items():
            for keyword in keywords:
                if keyword in article_content.lower():
                    found_keywords.append(category)
                    break
        
        # ページ内容とマッチング
        relevant_pages = []
        for page in pages:
            page_text = page['text'].lower()
            page_keywords = []
            
            for category, keywords in keyword_mappings.items():
                for keyword in keywords:
                    if keyword in page_text:
                        page_keywords.append(category)
                        break
            
            # 記事のキーワードとページのキーワードが重複する場合
            if any(kw in found_keywords for kw in page_keywords):
                relevant_pages.append({
                    "page_number": page['page'],
                    "keywords": page_keywords,
                    "image_path": f"images/p{page['page']:03d}.png"
                })
        
        # 重複を除去し、関連度順にソート
        unique_pages = []
        seen_pages = set()
        for page in relevant_pages:
            if page['page_number'] not in seen_pages:
                unique_pages.append(page)
                seen_pages.add(page['page_number'])
        
        return unique_pages[:5]  # 最大5枚まで
    
    def embed_images_in_article(self, article_content: str, relevant_images: List[Dict[str, Any]]) -> str:
        """記事に画像を埋め込む"""
        
        # 記事のセクションごとに画像を配置
        sections = article_content.split('\n## ')
        result_sections = []
        
        for i, section in enumerate(sections):
            result_sections.append(section)
            
            # 各セクションの後に適切な画像を配置
            if i < len(relevant_images) and i < len(sections) - 1:  # 最後のセクション以外
                image = relevant_images[i]
                image_tag = f"\n\n![{image['keywords'][0] if image['keywords'] else '関連画像'}]({image['image_path']})\n"
                result_sections.append(image_tag)
        
        return '\n## '.join(result_sections)
    
    def create_image_gallery(self, relevant_images: List[Dict[str, Any]]) -> str:
        """画像ギャラリーセクションを作成"""
        if not relevant_images:
            return ""
        
        gallery_content = "\n## 関連画像\n\n"
        for image in relevant_images:
            gallery_content += f"![ページ{image['page_number']}]({image['image_path']})\n"
        
        return gallery_content
