from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class BaseAIClient(ABC):
    """AI APIクライアントのベースクラス"""

    def __init__(self) -> None:
        self.last_usage: Optional[Dict[str, Any]] = None
        self.model_name: str = "unknown"

    def reset_usage(self) -> None:
        self.last_usage = None

    @abstractmethod
    def generate_analysis(self, prompt: str) -> str:
        """分析結果を生成"""
        raise NotImplementedError

    @abstractmethod
    def generate_summary(self, prompt: str) -> str:
        """サマリーを生成"""
        raise NotImplementedError

    @abstractmethod
    def generate_article(self, prompt: str) -> str:
        """記事を生成"""
        raise NotImplementedError


class MockAIClient(BaseAIClient):
    """テスト用のモックAIクライアント"""

    def __init__(self) -> None:
        super().__init__()
        self.model_name = "mock"

    def _set_mock_usage(self) -> None:
        self.last_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_tokens_details": {"cached_tokens": 0},
        }

    def generate_analysis(self, prompt: str) -> str:
        self._set_mock_usage()
        return (
            "分析概要: 決算資料を詳細に分析した結果、以下のポイントが確認されました。\n\n"
            "重要なポイント\n"
            "- 売上高は前年対比で成長を維持\n"
            "- 営業利益率の改善が見られる\n"
            "- 新規事業の貢献が拡大\n"
            "- 財務体質の健全性を維持\n\n"
            "関連ページ: ページ 3, 5, 8\n"
            "画像候補: ページ 3, 5, 8\n"
        )

    def generate_summary(self, prompt: str) -> str:
        self._set_mock_usage()
        return (
            "決算の要点:\n"
            "- 売上高は前年比で堅調な成長\n"
            "- 営業利益は改善傾向\n"
            "- 新規事業の貢献が拡大\n"
            "- 財務体質は健全で、投資余力も確保\n"
        )

    def generate_article(self, prompt: str) -> str:
        self._set_mock_usage()
        return (
            "# 決算分析記事（Mock版）\n\n"
            "## サマリー\n"
            "これは決算資料を詳細に分析した結果です。\n\n"
            "## 主要なポイント\n"
            "- 売上高の成長要因\n"
            "- 営業利益の改善\n"
            "- 新規事業の貢献\n"
            "- 財務健全性の維持\n\n"
            "## 投資判断\n"
            "総合評価: HOLD\n"
            "ターゲット価格: 要検討\n\n"
            "*この記事はMock AIによる生成結果です。実際のGPTを使用するとより詳細な分析が得られます。*\n"
        )


class OpenAIClient(BaseAIClient):
    """OpenAI APIクライアント"""

    RETRYABLE_STATUS = {429, 500, 502, 503, 504}

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.model_name = self.model
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "4"))
        self.retry_backoff = float(os.getenv("OPENAI_RETRY_BACKOFF", "1.8"))

        import openai  # type: ignore

        self._openai = openai
        self._client = openai.OpenAI(api_key=self.api_key)
        print(f"Using OpenAI model: {self.model}")

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}
        data: Dict[str, Any] = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
        details = getattr(usage, "prompt_tokens_details", None)
        if details:
            # `details` may be a pydantic model or dict-like object
            if hasattr(details, "model_dump"):
                data["prompt_tokens_details"] = details.model_dump()
            elif hasattr(details, "to_dict"):
                data["prompt_tokens_details"] = details.to_dict()
            else:
                data["prompt_tokens_details"] = dict(details)
        else:
            data["prompt_tokens_details"] = {"cached_tokens": 0}
        return data

    def _should_retry(self, error: Exception) -> bool:
        status = getattr(error, "status_code", None) or getattr(error, "http_status", None)
        if status in self.RETRYABLE_STATUS:
            return True
        error_type = type(error).__name__
        return error_type in {"RateLimitError", "APITimeoutError"}

    def _chat_completion(self, prompt: str, *, max_tokens: int, temperature: float) -> str:
        self.reset_usage()
        attempt = 0
        delay = 1.0
        while True:
            try:
                # GPT-5ではtemperatureパラメータを制限、その他は通常通り
                if self.model.startswith("gpt-5"):
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=max_tokens,
                        # temperatureパラメータを省略（GPT-5ではデフォルト値1のみサポート）
                    )
                else:
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=max_tokens,
                        temperature=temperature,
                    )
                content = response.choices[0].message.content if response.choices else None
                if not content or not content.strip():
                    raise ValueError("OpenAI returned empty response content")
                self.last_usage = self._extract_usage(response)
                return content
            except self._openai.RateLimitError as exc:  # type: ignore[attr-defined]
                attempt += 1
                if attempt > self.max_retries:
                    raise
                time.sleep(delay)
                delay *= self.retry_backoff
            except self._openai.APIError as exc:  # type: ignore[attr-defined]
                if not self._should_retry(exc):
                    raise
                attempt += 1
                if attempt > self.max_retries:
                    raise
                time.sleep(delay)
                delay *= self.retry_backoff
            except Exception:
                raise

    def generate_analysis(self, prompt: str) -> str:
        from ai_utils import generate_analysis
        return generate_analysis(prompt, model=self.model, api_key=self.api_key)

    def generate_summary(self, prompt: str) -> str:
        from ai_utils import generate_summary
        return generate_summary(prompt, model=self.model, api_key=self.api_key)

    def generate_article(self, prompt: str) -> str:
        from ai_utils import generate_article
        return generate_article(prompt, model=self.model, api_key=self.api_key)


def get_ai_client(provider: str = "mock") -> BaseAIClient:
    """AIクライアントを取得"""
    if provider == "openai":
        return OpenAIClient()
    if provider == "mock":
        return MockAIClient()
    raise ValueError(f"Unsupported AI provider: {provider}")
