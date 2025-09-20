"""
AI呼び出しの共通ユーティリティ関数
GPT-5のパラメータ制限に統一対応
"""
import os
from typing import Optional
from openai import OpenAI


def create_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """OpenAIクライアントを作成"""
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key is required")
    return OpenAI(api_key=api_key)


def call_openai_api(
    prompt: str, 
    model: Optional[str] = None,
    max_tokens: int = 1200,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None
) -> str:
    """
    OpenAI APIを呼び出す共通関数
    GPT-5の制限に自動対応
    
    Args:
        prompt: プロンプトテキスト
        model: 使用するモデル（省略時は環境変数から取得）
        max_tokens: 最大トークン数
        temperature: 温度パラメータ（GPT-5では無視される）
        api_key: APIキー（省略時は環境変数から取得）
    
    Returns:
        AIの応答テキスト
    
    Raises:
        ValueError: APIキーが設定されていない場合
        Exception: API呼び出しでエラーが発生した場合
    """
    try:
        client = create_openai_client(api_key)
        model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        # プロンプトのクリーニング（末尾の改行・空白を除去）
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise ValueError("Empty prompt provided")
        
        # GPT-5では長すぎるプロンプトを短縮（既知の問題回避）
        if model.startswith("gpt-5") and len(cleaned_prompt) > 10000:
            print(f"[WARNING] GPT-5: プロンプトが長すぎます ({len(cleaned_prompt)} chars)。短縮します。")
            # プロンプトを前半と後半に分けて中央部分を省略
            prefix = cleaned_prompt[:4000]
            suffix = cleaned_prompt[-4000:]
            cleaned_prompt = f"{prefix}\n\n[中間部分省略]\n\n{suffix}"
            print(f"[INFO] プロンプト短縮後: {len(cleaned_prompt)} chars")
        
        print(f"[DEBUG] Model: {model}, Prompt length: {len(cleaned_prompt)} chars")
        
        # GPT-5の制限に対応
        if model.startswith("gpt-5"):
            # GPT-5では確実な応答を促すためシステムメッセージを追加
            # 長いコンテンツはキャッシュ機能を使用
            if len(cleaned_prompt) > 8000:
                # 長いプロンプトをキャッシュ対応のメッセージ構造に変換
                messages = [
                    {"role": "system", "content": "あなたは詳細で有用な分析を提供する専門家です。必ず具体的で詳細な回答を生成してください。"},
                    {"role": "user", "content": cleaned_prompt, "cache_control": {"type": "ephemeral"}}
                ]
            else:
                messages = [
                    {"role": "system", "content": "あなたは詳細で有用な分析を提供する専門家です。必ず具体的で詳細な回答を生成してください。"},
                    {"role": "user", "content": cleaned_prompt}
                ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_tokens,
                # temperatureは省略（デフォルト値1のみサポート）
            )
        else:
            # その他のモデルは通常通り
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": cleaned_prompt}],
                max_completion_tokens=max_tokens,
                temperature=temperature or 0.3,
            )
        
        # レスポンスの詳細をデバッグ出力
        print(f"[DEBUG] Response finish_reason: {response.choices[0].finish_reason}")
        print(f"[DEBUG] Response content length: {len(response.choices[0].message.content or '')}")
        
        # トークン使用量をデバッグ出力
        usage = response.usage
        if usage:
            print(f"[DEBUG] Tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        content = response.choices[0].message.content
        if not content or not content.strip():
            # コンテンツフィルターの確認
            if response.choices[0].finish_reason == "content_filter":
                raise ValueError("Content was filtered by OpenAI safety systems")
            else:
                raise ValueError(f"OpenAI returned empty response content (finish_reason: {response.choices[0].finish_reason})")
        
        # トークン使用量情報を含む辞書を返す
        return {
            "content": content.strip(),
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0
            }
        }
        
    except Exception as e:
        error_msg = f"AI API呼び出しエラー: {str(e)}"
        print(f"エラー詳細: {error_msg}")
        # エラー時は文字列を返す（ai_client.pyで適切に処理される）
        return error_msg


def generate_analysis(prompt: str, **kwargs) -> str:
    """分析用AI呼び出し（GPT-5対応で大幅増量）"""
    model = kwargs.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4o')
    if model.startswith("gpt-5"):
        # GPT-5では大幅に増量（推論トークンを考慮）
        return call_openai_api(prompt, max_tokens=8000, **kwargs)
    else:
        return call_openai_api(prompt, max_tokens=1200, **kwargs)


def generate_summary(prompt: str, **kwargs) -> str:
    """サマリー用AI呼び出し（GPT-5対応）"""
    model = kwargs.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4o')
    if model.startswith("gpt-5"):
        return call_openai_api(prompt, max_tokens=4000, **kwargs)
    else:
        return call_openai_api(prompt, max_tokens=600, **kwargs)


def generate_article(prompt: str, **kwargs) -> str:
    """記事用AI呼び出し（GPT-5対応で最大増量）"""
    model = kwargs.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4o')
    if model.startswith("gpt-5"):
        return call_openai_api(prompt, max_tokens=12000, **kwargs)
    else:
        return call_openai_api(prompt, max_tokens=4096, **kwargs)
