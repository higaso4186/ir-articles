from __future__ import annotations
import os
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

class BaseAIClient(ABC):
    """AI APIクライアントのベースクラス"""
    
    @abstractmethod
    def generate_analysis(self, prompt: str) -> str:
        """分析結果を生成"""
        pass
    
    @abstractmethod
    def generate_summary(self, prompt: str) -> str:
        """サマリーを生成"""
        pass
    
    @abstractmethod
    def generate_article(self, prompt: str) -> str:
        """記事を生成"""
        pass

class MockAIClient(BaseAIClient):
    """テスト用のモックAIクライアント"""
    
    def generate_analysis(self, prompt: str) -> str:
        return f"""
分析内容: 決算資料を詳細に分析した結果、以下のポイントが確認されました。

重要なポイント:
- 売上高は前期比で成長を維持
- 営業利益率の改善が見られる
- 新規事業の貢献が拡大
- 財務体質の健全性を維持

関連ページ: ページ 3, 5, 8
画像候補: ページ 3, 5, 8
"""
    
    def generate_summary(self, prompt: str) -> str:
        return """
決算の要点:
- 売上高は前期比で堅調な成長を維持
- 営業利益は改善傾向を示している
- 新規事業の貢献が拡大し、成長ドライバーとして機能
- 財務体質は健全で、投資余力も確保されている
"""
    
    def generate_article(self, prompt: str) -> str:
        return """
# 決算分析記事（Mock版）

## サマリー
この記事は決算資料を詳細に分析した結果です。

## 主要なポイント
- 売上高の成長要因
- 営業利益の改善
- 新規事業の貢献
- 財務健全性の維持

## 投資判断
総合評価: HOLD
ターゲット価格: 要検討

*この記事はMock AIにより生成されました。実際のGPTを使用するとより詳細な分析が得られます。
"""

class OpenAIClient(BaseAIClient):
    """OpenAI APIクライアント"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # GPTモデルバージョンを環境変数から取得（デフォルト: gpt-4o）
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        print(f"Using OpenAI model: {self.model}")
    
    def generate_analysis(self, prompt: str) -> str:
        # OpenAI API呼び出しの実装
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,  # 環境変数から取得したモデルを使用
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3  # より一貫した結果のため
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI分析エラー: {str(e)}"
    
    def generate_summary(self, prompt: str) -> str:
        # OpenAI API呼び出しの実装
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,  # 環境変数から取得したモデルを使用
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3  # より一貫した結果のため
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AIサマリーエラー: {str(e)}"
    
    def generate_article(self, prompt: str) -> str:
        # OpenAI API呼び出しの実装
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,  # 環境変数から取得したモデルを使用
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # 記事生成のため多めに設定
                temperature=0.3  # より一貫した結果のため
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI記事生成エラー: {str(e)}"

def get_ai_client(provider: str = "mock") -> BaseAIClient:
    """AIクライアントを取得"""
    if provider == "openai":
        return OpenAIClient()
    elif provider == "mock":
        return MockAIClient()
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
