import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class EvidenceReference(BaseModel):
    component: str
    reference: str


class StructuredReasoning(BaseModel):
    market_summary: str
    bull_case: List[str] = Field(default_factory=list, max_length=8)
    bear_case: List[str] = Field(default_factory=list, max_length=8)
    key_risks: List[str] = Field(default_factory=list, max_length=8)
    portfolio_context: str
    important_upcoming_events: List[str] = Field(default_factory=list, max_length=8)
    thesis_invalidation_conditions: List[str] = Field(default_factory=list, max_length=8)
    evidence_used: List[EvidenceReference] = Field(default_factory=list, max_length=20)
    data_limitations: List[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def reject_prohibited_advice(self):
        text = self.model_dump_json().lower()
        prohibited = (
            r"\bguaranteed returns?\b", r"\bprice targets?\b", r"\bprofit predictions?\b",
            r"\bstrong buy\b", r"\bstrong sell\b", r"\bexecute (a )?trade\b",
            r"\byou should buy\b", r"\byou should sell\b",
        )
        if any(re.search(pattern, text) for pattern in prohibited):
            raise ValueError("Reasoning contains prohibited recommendation or return language")
        return self


class AIStatusResponse(BaseModel):
    enabled: bool
    configured: bool
    provider_status: str
    ai_provider: str
    ai_model: str
    last_analysis_generated_at: Optional[datetime] = None


class AIAnalysisResponse(BaseModel):
    asset: str
    status: str
    provider_status: str
    ai_provider: str
    ai_model: str
    analysis_generated_at: Optional[datetime] = None
    evidence_fingerprint: str
    cached: bool = False
    reasoning: Optional[StructuredReasoning] = None
    data_limitations: List[str] = Field(default_factory=list)
