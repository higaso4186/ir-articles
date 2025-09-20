"""
PDFテキストの要約とGPT-5対応の前処理
"""
import re
from typing import List, Dict, Any


def extract_key_sections(pages: List[Dict]) -> Dict[str, str]:
    """
    PDFページから重要なセクションを抽出
    GPT-5の制限に対応するため、全テキストではなく要約を生成
    """
    sections = {
        "業績概要": "",
        "財務数値": "",
        "戦略・展望": "",
        "リスク要因": "",
        "セグメント情報": ""
    }
    
    all_text = ""
    for page in pages[:15]:  # 最初の15ページのみ処理
        all_text += page.get('text', '') + "\n"
    
    # 重要な数値パターンを抽出
    financial_patterns = [
        r'売上高[：:\s]*[\d,]+(?:百万円|億円|千円)',
        r'営業利益[：:\s]*[\d,]+(?:百万円|億円|千円)',
        r'純利益[：:\s]*[\d,]+(?:百万円|億円|千円)',
        r'前年同期比[：:\s]*[\d.]+%',
        r'増減[：:\s]*[\d.]+%'
    ]
    
    financial_data = []
    for pattern in financial_patterns:
        matches = re.findall(pattern, all_text)
        financial_data.extend(matches)
    
    sections["財務数値"] = "\n".join(financial_data[:10])  # 最大10項目
    
    # セクション別にキーワードで分類
    keywords = {
        "業績概要": ["売上", "利益", "業績", "決算", "概要"],
        "戦略・展望": ["戦略", "方針", "計画", "展望", "目標"],
        "リスク要因": ["リスク", "課題", "懸念", "影響", "対策"],
        "セグメント情報": ["セグメント", "事業", "部門", "分野"]
    }
    
    for section, words in keywords.items():
        relevant_text = []
        for page in pages[:10]:
            text = page.get('text', '')
            for word in words:
                if word in text:
                    # 該当する段落を抽出（前後100文字）
                    matches = re.finditer(rf'.{{0,100}}{re.escape(word)}.{{0,100}}', text)
                    for match in matches:
                        relevant_text.append(match.group().strip())
        
        # 重複を除去して最大5項目
        unique_text = list(set(relevant_text))[:5]
        sections[section] = "\n".join(unique_text)
    
    return sections


def create_compact_prompt(base_prompt: str, pages: List[Dict], company_name: str = "不明企業") -> str:
    """
    GPT-5用にコンパクトなプロンプトを生成
    全PDFテキストではなく、要約された重要情報のみを含める
    """
    # 重要セクションを抽出
    sections = extract_key_sections(pages)
    
    # コンパクトな企業情報を構築
    compact_info = f"""
## 分析対象企業情報

**企業名**: {company_name}

### 主要財務数値
{sections['財務数値'] or '数値情報の抽出に失敗しました'}

### 業績概要
{sections['業績概要'][:500] or '業績情報の抽出に失敗しました'}

### 戦略・展望
{sections['戦略・展望'][:400] or '戦略情報の抽出に失敗しました'}

### セグメント情報
{sections['セグメント情報'][:300] or 'セグメント情報の抽出に失敗しました'}

### リスク要因
{sections['リスク要因'][:300] or 'リスク情報の抽出に失敗しました'}

---

上記の決算資料情報をもとに、詳細な分析を行ってください。
"""
    
    # ベースプロンプトと組み合わせ
    final_prompt = f"{base_prompt}\n{compact_info}"
    
    # 最終的な長さチェック
    if len(final_prompt) > 8000:
        # さらに短縮
        compact_info = f"""
## 分析対象: {company_name}

### 主要数値
{sections['財務数値'][:200]}

### 業績概要
{sections['業績概要'][:300]}

### その他重要情報
{sections['戦略・展望'][:200]}

上記をもとに分析してください。
"""
        final_prompt = f"{base_prompt}\n{compact_info}"
    
    return final_prompt
