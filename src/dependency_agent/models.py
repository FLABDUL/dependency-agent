from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class Evidence:
    source: str
    detail: str
    value: str


@dataclass(frozen=True)
class SuggestedChange:
    file: str
    summary: str
    before: str
    after: str
    diff: str


@dataclass(frozen=True)
class AnalysisResult:
    status: Literal["conflict", "compatible", "unsupported"]
    headline: str
    summary: str
    confidence: Literal["high", "medium", "low"]
    evidence: tuple[Evidence, ...]
    suggestion: SuggestedChange | None
    verification: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
