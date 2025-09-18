\
from __future__ import annotations
import re
from typing import List, Tuple, Optional
from schema import CommonInfo, KPIValue, SegmentEntry

JP_NUM = r"[0-9０-９,，\.]+"  # Japanese digits variants

def _find_company_name(pages: List[dict]) -> Tuple[Optional[str], List[int]]:
    # Heuristic: first 3 pages, look for '株式会社' or 'Company Name'
    pattern = re.compile(r"(株式会社[^\s\n　]+)")
    for p in pages[:3]:
        m = pattern.search(p['text'])
        if m:
            return m.group(1), [p['page']]
    # fallback: first non-empty line
    for p in pages[:2]:
        for line in p['text'].splitlines():
            line = line.strip()
            if line:
                return line[:50], [p['page']]
    return None, []

def _find_period(pages: List[dict]) -> Tuple[Optional[str], Optional[str], List[int]]:
    # Examples: 2025年3月期 第1四半期 / FY2025 Q1
    patt1 = re.compile(r"(\d{4})年\s*(\d{1,2})月期\s*第?(\d)四半期")
    patt2 = re.compile(r"FY\s?(\d{4}).{0,5}Q\s?([1-4])", re.IGNORECASE)
    for p in pages[:5]:
        t = p['text']
        m = patt1.search(t)
        if m:
            year, month, q = m.groups()
            return year, f"FY{year} Q{q}", [p['page']]
        m2 = patt2.search(t)
        if m2:
            year, q = m2.groups()
            return year, f"FY{year} Q{q}", [p['page']]
    return None, None, []

def _find_accounting_standard(pages: List[dict]) -> Tuple[Optional[str], List[int]]:
    mapping = {
        r"IFRS": "IFRS",
        r"国際会計基準": "IFRS",
        r"日本基準|日本会計基準|J-GAAP|JGAAP": "JGAAP",
        r"US[-\s]?GAAP|米国会計基準": "US-GAAP",
    }
    cites = []
    for p in pages[:5]:
        for pat, label in mapping.items():
            if re.search(pat, p['text'], re.IGNORECASE):
                cites.append(p['page'])
                return label, list(set(cites))
    return None, []

def _find_currency_unit(pages: List[dict]) -> Tuple[Optional[str], Optional[str], List[int]]:
    # Look for '百万円', '千円', '円', 'JPY', 'USD'
    for p in pages[:5]:
        t = p['text']
        if '百万円' in t:
            cur = 'JPY'; unit = 'million'
            return cur, unit, [p['page']]
        if '千円' in t:
            cur = 'JPY'; unit = 'thousand'
            return cur, unit, [p['page']]
        if '円' in t:
            cur = 'JPY'; unit = 'one'
            return cur, unit, [p['page']]
        if re.search(r"\bUSD\b", t):
            return 'USD', 'million', [p['page']]
        if re.search(r"\bJPY\b", t):
            return 'JPY', 'million', [p['page']]
    return None, None, []

def _norm_number(s: str, unit: Optional[str]) -> int:
    # Remove commas and fullwidth
    trans = str.maketrans("０１２３４５６７８９，", "0123456789,")
    s = s.translate(trans).replace(',', '')
    val = int(float(s))
    mult = 1
    if unit == 'million':
        mult = 1_000_000
    elif unit == 'thousand':
        mult = 1_000
    return val * mult

def _find_kpi(pages: List[dict], unit: Optional[str]) -> dict:
    # Look for labels with numbers near them
    patterns = [
        ('revenue', r"(売上高|売上収益|Revenue)[^\n]{0,20}(" + JP_NUM + ")"),
        ('operating_income', r"(営業利益|営業損益|Operating\s*income)[^\n]{0,20}(" + JP_NUM + ")"),
        ('ebitda', r"(EBITDA|EBITDA等?)[^\n]{0,20}(" + JP_NUM + ")"),
    ]
    result = {}
    for key, pat in patterns:
        regex = re.compile(pat, re.IGNORECASE)
        for p in pages[:8]:
            m = regex.search(p['text'])
            if m:
                num = _norm_number(m.group(2), unit)
                result[key] = KPIValue(value=num, page_citations=[p['page']])
                break
        if key not in result:
            result[key] = KPIValue(value=None, page_citations=[])
    return result

def _find_segments(pages: List[dict], unit: Optional[str]) -> list[SegmentEntry]:
    # Heuristic: lines containing 'セグメント' or headings with katakana/English words followed by 数字
    segs = []
    seen = set()
    patt_line = re.compile(r"(?P<name>[A-Za-z\u30A0-\u30FF一-龥ー]{2,20})[^\n]{0,10}(" + r"[0-9０-９,，\.]+" + r")")
    for p in pages[:10]:
        for line in p['text'].splitlines():
            if 'セグメント' in line or 'segment' in line.lower():
                m = patt_line.search(line)
                if m:
                    name = m.group('name').strip()
                    if name not in seen:
                        seen.add(name)
                        # revenue optional
                        try:
                            num = re.findall(r"[0-9０-９,，\.]+", line)[-1]
                            revenue = _norm_number(num, unit)
                        except Exception:
                            revenue = None
                        segs.append(SegmentEntry(name=name, revenue=revenue, page_citations=[p['page']]))
    return segs[:3]

def extract_common(pages: List[dict]) -> CommonInfo:
    company, c_pages = _find_company_name(pages)
    fiscal_year, period_label, fy_pages = _find_period(pages)
    acc, acc_pages = _find_accounting_standard(pages)
    cur, unit, cu_pages = _find_currency_unit(pages)
    kpis = _find_kpi(pages, unit)
    segs = _find_segments(pages, unit)

    all_common = CommonInfo(
        company_name=company,
        fiscal_year=fiscal_year,
        period_label=period_label,
        accounting_standard=acc,
        currency=cur,
        unit=unit,
        kpis=kpis,
        segments=segs
    )
    return all_common
