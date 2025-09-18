from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional


class PromptLoader:
    """プロンプトファイルを読み込むクラス"""

    def __init__(self, prompt_dir: Path | None = None):
        self.prompt_dir = Path(prompt_dir) if prompt_dir else Path(__file__).parent.parent / "prompt"

    def load_prompt(self, filename: str) -> str:
        prompt_path = self.prompt_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def load_article_prompt(self) -> str:
        return self.load_prompt("決算書分析記事作成プロンプト.md")

    def load_overview_prompt(self) -> str:
        return self.load_prompt("概要生成.md")

    def load_slot_prompt(self, slot_number: int) -> str:
        slot_files = {
            1: "slot1_業績分析.md",
            2: "slot2_セグメント分析.md",
            3: "slot3_財務健全性.md",
            4: "slot4_戦略展望.md",
            5: "slot5_リスク分析.md",
        }
        if slot_number not in slot_files:
            raise ValueError(f"Invalid slot number: {slot_number}")
        return self.load_prompt(slot_files[slot_number])

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
        text_content = self._collect_text_snippet(pages)
        sections = [base_prompt, self._build_metadata_section(metadata), self._build_guidance_section(slot_number, metadata)]
        sections.append("## 決算書のテキスト内容\n" + text_content)
        sections.append("上記の決算書を詳細に分析し、指定された観点に従って定量・定性のバランスを意識したレポートを作成してください。引用ページと根拠数値を明示してください。")
        return "\n".join(section for section in sections if section)

