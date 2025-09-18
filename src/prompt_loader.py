from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

class PromptLoader:
    """プロンプトファイルを読み込むクラス"""
    
    def __init__(self, prompt_dir: Path = None):
        if prompt_dir is None:
            self.prompt_dir = Path(__file__).parent.parent / "prompt"
        else:
            self.prompt_dir = Path(prompt_dir)
    
    def load_prompt(self, filename: str) -> str:
        """プロンプトファイルを読み込む"""
        prompt_path = self.prompt_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        return prompt_path.read_text(encoding='utf-8')
    
    def load_article_prompt(self) -> str:
        """決算書分析記事作成プロンプトを読み込む"""
        return self.load_prompt("決算書分析記事作成プロンプト.md")
    
    def load_overview_prompt(self) -> str:
        """概要生成プロンプトを読み込む"""
        return self.load_prompt("概要生成.md")
    
    def load_slot_prompt(self, slot_number: int) -> str:
        """スロット専用プロンプトを読み込む"""
        slot_files = {
            1: "slot1_業績分析.md",
            2: "slot2_セグメント分析.md", 
            3: "slot3_財務健全性.md",
            4: "slot4_戦略展望.md",
            5: "slot5_リスク分析.md"
        }
        
        if slot_number not in slot_files:
            raise ValueError(f"Invalid slot number: {slot_number}")
        
        return self.load_prompt(slot_files[slot_number])
    
    def create_overview_prompt(self, pages: list, company_name: str = "不明企業") -> str:
        """概要生成用のプロンプトを作成"""
        base_prompt = self.load_overview_prompt()
        
        # 最初の10ページのテキストを結合
        text_content = ""
        for page in pages[:10]:
            text_content += f"--- ページ {page['page']} ---\n"
            text_content += page['text'] + "\n\n"
        
        full_prompt = f"""
{base_prompt}

## 分析対象の決算資料

**企業名**: {company_name}

**決算資料のテキスト内容**:
{text_content}

上記の決算資料を分析し、記事の概要・冒頭部分を作成してください。
"""
        
        return full_prompt
    
    def create_slot_prompt(self, slot_number: int, pages: list, company_name: str = "不明企業") -> str:
        """スロット分析用のプロンプトを作成"""
        base_prompt = self.load_slot_prompt(slot_number)
        
        # 全ページのテキストを結合
        text_content = ""
        for page in pages:
            text_content += f"--- ページ {page['page']} ---\n"
            text_content += page['text'] + "\n\n"
        
        full_prompt = f"""
{base_prompt}

## 分析対象の決算資料

**企業名**: {company_name}

**決算資料のテキスト内容**:
{text_content}

上記の決算資料を詳細に分析し、指定された分析観点に従って詳細な分析を行ってください。
"""
        
        return full_prompt
