# IR MD Pipeline (Local Python)

**目的**: 決算PDFをローカルで処理し、ページ画像を埋め込んだ Markdown を生成します。
- PDF → 画像化（ページごと）
- テキスト抽出（PyMuPDF）
- 共通情報抽出（正規表現ベース：会社名、決算期、通貨・単位、主要KPI）
- 3つの分析モジュール（正規表現・頻度ベース）
  - KPIサマリ
  - セグメントっぽい見出しの抽出（頻度）
  - リスク記述の抽出
- 引用ページ番号を明示し、該当ページ画像をMarkdownに埋め込み
- 生成物：`outputs/review.md` + `images/` + 中間JSON

## 前提
- Python 3.10+
- `pip install -r requirements.txt`
- （任意）OCRが必要なPDF用に`tesseract`をOSにインストールしておくと精度が上がります。
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get update && sudo apt-get install -y tesseract-ocr`

## 使い方

### 1. 基本セットアップ
```bash
python -m venv .venv && source .venv/bin/activate  # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数設定
```bash
# env.exampleをコピーして.envファイルを作成
cp env.example .env

# .envファイルを編集して以下を設定:
# OPENAI_API_KEY=sk-your-api-key-here
# OPENAI_MODEL=gpt-4o  # 使用したいGPTモデル
# AI_PROVIDER=openai
```

**利用可能なOpenAIモデル:**
- `gpt-4o` (最新・推奨、高品質)
- `gpt-4o-mini` (コスト重視、高速)
- `gpt-4-turbo` (高性能)
- `gpt-3.5-turbo` (コスト重視・高速)

### 3. 実行
```bash
# 基本パイプライン（ローカル分析のみ）
python src/main.py --pdf /path/to/input.pdf --outdir ./runs/sample1

# AI強化パイプライン（推奨）
python src/enhanced_main.py --pdf /path/to/input.pdf --outdir ./runs/enhanced1 --ai-provider openai
```

## 出力構成（例）
```
runs/sample1/
  source.pdf
  images/
    p001.png
    p002.png
  extracted/
    pages.jsonl           # ページ別テキスト
    common.json           # 共通情報（抽出結果）
    analyses.json         # 3分析の結果
  outputs/
    review.md             # note向けMarkdown
  logs/
    run.json              # 実行メタデータ
```

## 注意
- 本実装は**ローカルのみ**で完結し、外部APIを利用しません（安定動作を重視）。
- フォーマットが多様なIR PDFに対しては、正規表現ベース抽出が**完全一致**しない場合があります。
  - ただし、**処理自体は必ず成功**するように例外を吸収し、該当値は `null` にフォールバックします。
- 高精度化が必要になれば、`src/analyzers.py` にモジュールを追加して拡張可能です。
