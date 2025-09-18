from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class KPIValue(BaseModel):
    value: Optional[int] = None
    page_citations: List[int] = Field(default_factory=list)

class SegmentEntry(BaseModel):
    name: str
    revenue: Optional[int] = None
    page_citations: List[int] = Field(default_factory=list)

class CommonInfo(BaseModel):
    company_name: Optional[str] = None
    fiscal_year: Optional[str] = None
    period_label: Optional[str] = None
    accounting_standard: Optional[str] = None  # IFRS/JGAAP/US-GAAP/Other
    currency: Optional[str] = None             # e.g., JPY, USD
    unit: Optional[str] = None                 # million/thousand/one
    kpis: Dict[str, KPIValue] = Field(default_factory=dict)
    segments: List[SegmentEntry] = Field(default_factory=list)

class AnalysisItem(BaseModel):
    id: str
    title: str
    finding: str
    page_citations: List[int] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)

class DocMeta(BaseModel):
    doc_id: str
    filename: str
    pages: int

class PipelineResult(BaseModel):
    meta: DocMeta
    common: CommonInfo
    analyses: List[AnalysisItem]
