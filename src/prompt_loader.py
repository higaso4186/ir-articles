from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib


class PromptLoader:
    """プロンプトファイルを読み込むクラス"""

    def __init__(self, prompt_dir: Path | None = None):
        self.prompt_dir = Path(prompt_dir) if prompt_dir else Path(__file__).parent.parent / "prompt"
        self._cache: Dict[str, str] = {}
        self._version_cache: Dict[str, str] = {}
        self._slot_files = {
            1: "slot1_業績分析.md",
            2: "slot2_セグメント分析.md",
            3: "slot3_財務健全性.md",
            4: "slot4_戦略展望.md",
            5: "slot5_リスク分析.md",
        }

    def _resolve(self, filename: str) -> Path:
        return self.prompt_dir / filename

    def load_prompt(self, filename: str) -> str:
        if filename in self._cache:
            return self._cache[filename]
        prompt_path = self._resolve(filename)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        text = prompt_path.read_text(encoding="utf-8")
        self._cache[filename] = text
        return text

    def load_article_prompt(self) -> str:
        return self.load_prompt("決算書分析記事作成プロンプト.md")

    def load_article_template(self) -> str:
        return self.load_prompt("article_template.md")

    def load_overview_prompt(self) -> str:
        return self.load_prompt("概要生成.md")

    def load_slot_prompt(self, slot_number: int) -> str:
        return self.load_prompt(self.get_slot_filename(slot_number))

    def get_slot_filename(self, slot_number: int) -> str:
        if slot_number not in self._slot_files:
            raise ValueError(f"Invalid slot number: {slot_number}")
        return self._slot_files[slot_number]

    def get_prompt_version(self, filename: str) -> str:
        if filename in self._version_cache:
            return self._version_cache[filename]
        content = self.load_prompt(filename)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        self._version_cache[filename] = digest
        return digest

    def _build_metadata_section(self, metadata: Dict[str, Any] | None) -> str:
        if not metadata:
            return ""
        company = metadata.get("company_name", "不明企業")
        industry = metadata.get("industry", "業界不明")
        period = metadata.get("period_label") or metadata.get("fiscal_year") or "期間情報不明"
        kpi_summary = metadata.get("kpi_summary") or "主要KPI情報が取得できていません"
        segments = ", ".join(metadata.get("segments", [])[:5]) or "セグメント情報が限定的"
        accounting = metadata.get("accounting_standard") or "会計基準不明"
        lines = [
            "## 企業メタ情報",
            f"- 企業名: {company}",
            f"- 業界: {industry}",
            f"- 会計基準: {accounting}",
            f"- 対象期間: {period}",
            f"- 主要KPI: {kpi_summary}",
            f"- 主なセグメント: {segments}",
        ]
        return "\n".join(lines) + "\n\n"

    def _build_guidance_section(self, slot_number: Optional[int], metadata: Dict[str, Any] | None) -> str:
        if not metadata:
            return ""
        if slot_number is None:
            overview_guidance = metadata.get("overview_guidance")
            return f"## 補足指示\n{overview_guidance}\n\n" if overview_guidance else ""
        slot_guidance = (metadata.get("slot_guidance") or {}).get(slot_number)
        return f"## 補足指示\n{slot_guidance}\n\n" if slot_guidance else ""

    def _collect_text_snippet(self, pages: list[dict], limit: int | None = None) -> str:
        snippet = ""
        slice_pages = pages if limit is None else pages[:limit]
        for page in slice_pages:
            snippet += f"--- ページ {page['page']} ---\n"
            snippet += page.get("text", "") + "\n\n"
        return snippet

    def create_overview_prompt(self, pages: list, metadata: Dict[str, Any] | None = None) -> str:
        base_prompt = self.load_overview_prompt()
        text_content = self._collect_text_snippet(pages, limit=10)
        sections = [base_prompt, self._build_metadata_section(metadata), self._build_guidance_section(None, metadata)]
        sections.append("## 決算書のテキスト内容\n" + text_content)
        sections.append("上記のテキストを分析し、記事冒頭に掲載する高品質な概要を作成してください。読者が企業の状況を素早く把握できるよう、数値と要点を3〜4項目に整理してください。")
        return "\n".join(section for section in sections if section)

    def create_slot_prompt(self, slot_number: int, pages: list, metadata: Dict[str, Any] | None = None) -> str:
        base_prompt = self.load_slot_prompt(slot_number)
        
        # GPT-5対応: 長いプロンプトを要約してコンパクト化
        import os
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        if model.startswith("gpt-5"):
            # GPT-5では要約版を使用
            from pdf_summarizer import create_compact_prompt
            company_name = metadata.get("company_name", "不明企業") if metadata else "不明企業"
            return create_compact_prompt(base_prompt, pages, company_name)
        else:
            # その他のモデルでは従来通り
            text_content = self._collect_text_snippet(pages)
            sections = [base_prompt, self._build_metadata_section(metadata), self._build_guidance_section(slot_number, metadata)]
            sections.append("## 決算書のテキスト内容\n" + text_content)
            sections.append("上記の決算書を詳細に分析し、指定された観点に従って定量・定性のバランスを意識したレポートを作成してください。引用ページと根拠数値を明示してください。")
            return "\n".join(section for section in sections if section)

    def create_image_caption_prompt(
        self,
        slot_number: int,
        slot_name: str,
        slot_summary: str,
        image_context: list[dict[str, Any]],
        metadata: Dict[str, Any] | None,
    ) -> str:
        base_prompt = self.load_prompt("画像キャプション生成.md")
        company = metadata.get("company_name", "不明企業") if metadata else "不明企業"
        period = metadata.get("period_label") or metadata.get("fiscal_year") or "期間情報不明" if metadata else "期間情報不明"
        industry = metadata.get("industry", "業界不明") if metadata else "業界不明"
        image_bullets = "\n".join(
            f"  - {ctx.get('image', 'N/A')} (P{ctx.get('page', '??')})" for ctx in image_context
        ) or "  - 画像情報なし"
        excerpts = []
        for ctx in image_context:
            page = ctx.get('page')
            excerpt = ctx.get('excerpt', '').strip()
            if excerpt:
                prefix = f"[P{page:02d}] " if isinstance(page, int) else ""
                excerpts.append(prefix + excerpt)
        text_excerpt = "\n".join(excerpts) or "該当ページのテキストが取得できませんでした。"
        return base_prompt.format(
            slot_number=slot_number,
            slot_name=slot_name,
            slot_summary=slot_summary,
            company_name=company,
            period_label=period,
            industry=industry,
            image_bullets=image_bullets,
            text_excerpt=text_excerpt,
        )

    def create_visual_highlight_prompt(
        self,
        metadata: Dict[str, Any],
        metric_rows: list[str],
        sparkline_hints: list[str],
        segment_highlights: list[str],
    ) -> str:
        base_prompt = self.load_prompt("ビジュアルハイライト生成.md")
        company = metadata.get("company_name", "不明企業")
        industry = metadata.get("industry", "業界不明")
        period = metadata.get("period_label") or metadata.get("fiscal_year") or "期間情報不明"
        currency = metadata.get("currency") or "N/A"
        unit_label = metadata.get("unit") or "N/A"
        metric_rows_str = "\n".join(metric_rows) or "- データなし"
        sparkline_str = "\n".join(sparkline_hints) or "- 傾向情報なし"
        segment_str = "\n".join(f"- {row}" for row in segment_highlights) or "- セグメント情報が限定的です"
        return base_prompt.format(
            company_name=company,
            industry=industry,
            period_label=period,
            currency=currency,
            unit_label=unit_label,
            metric_rows=metric_rows_str,
            kpi_commentary=metadata.get("kpi_summary") or "主要KPI情報が取得できていません",
            segment_highlights=segment_str,
            sparkline_hints=sparkline_str,
        )

    def create_closing_prompt(
        self,
        metadata: Dict[str, Any],
        analysis_bullets: list[str],
        investment_summary: str,
    ) -> str:
        base_prompt = self.load_prompt("締めセクション生成.md")
        company = metadata.get("company_name", "不明企業")
        industry = metadata.get("industry", "業界不明")
        period = metadata.get("period_label") or metadata.get("fiscal_year") or "期間情報不明"
        kpi_summary = metadata.get("kpi_summary") or "主要KPI情報が取得できていません"
        segment_highlights = metadata.get("segment_descriptions") or []
        segment_text = "\n".join(f"- {row}" for row in segment_highlights[:3]) or "- セグメントの詳細情報は限定的です"
        bullet_text = "\n".join(f"- {b}" for b in analysis_bullets[:5]) or "- 強調すべきポイントが抽出できませんでした"
        return base_prompt.format(
            company_name=company,
            industry=industry,
            period_label=period,
            kpi_summary=kpi_summary,
            segment_highlights=segment_text,
            analysis_bullets=bullet_text,
            investment_summary=investment_summary or "投資判断セクションで具体的な指摘がありません。",
        )


