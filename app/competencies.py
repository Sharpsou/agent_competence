from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, Field

from app.jobs import JobOffer, normalize_text
from app.settings import load_environment


class CompetencyCategory(StrEnum):
    TECHNICAL = "technical"
    METHOD = "method"
    TOOL = "tool"
    DOMAIN = "domain"
    LANGUAGE = "language"


class AgentStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class AgentTraceStep(BaseModel):
    agent_name: str
    status: AgentStatus
    message: str


class CompetencyOfferContext(BaseModel):
    source: str
    source_job_id: str
    title: str
    company_name: str


class CompetencyEvidence(BaseModel):
    source: str = "France Travail"
    name: str
    category: CompetencyCategory
    confidence: float = Field(ge=0, le=1)
    source_job_id: str
    title: str
    company_name: str
    matched_text: str


class CompetencySummary(BaseModel):
    name: str
    category: CompetencyCategory
    evidence_count: int
    confidence: float = Field(ge=0, le=1)
    offers: list[CompetencyOfferContext]


class CompetencyExtractionRequest(BaseModel):
    keyword: str
    job_title: str | None = None
    offers: list[JobOffer] = Field(default_factory=list)
    min_confidence: float = Field(default=0.45, ge=0, le=1)


class CompetencyExtractionResponse(BaseModel):
    run_id: str
    extracted_at: str
    keyword: str
    job_title: str | None
    offer_count: int
    competencies: list[CompetencySummary]
    agent_trace: list[AgentTraceStep]


@runtime_checkable
class JsonLlmClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]: ...


class CandidateExtractionAgent:
    name = "candidate_extractor"

    def extract(self, offers: list[JobOffer]) -> list[CompetencyEvidence]:
        evidence: list[CompetencyEvidence] = []
        for offer in offers:
            text = " ".join([offer.title, offer.description_text])
            normalized = normalize_text(text)
            for alias, definition in SKILL_ALIASES.items():
                if not alias_matches(alias, normalized):
                    continue
                evidence.append(
                    CompetencyEvidence(
                        name=definition.name,
                        source=offer.source,
                        category=definition.category,
                        confidence=definition.base_confidence,
                        source_job_id=offer.source_job_id,
                        title=offer.title,
                        company_name=offer.company_name,
                        matched_text=alias,
                    )
                )
        return evidence


class LlmCandidateExtractionAgent:
    name = "llm_candidate_extractor"

    def __init__(self, llm_client: JsonLlmClient) -> None:
        self.llm_client = llm_client

    def extract(self, request: CompetencyExtractionRequest) -> list[CompetencyEvidence]:
        payload = self.llm_client.complete_json(
            system_prompt=LLM_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=build_llm_extraction_prompt(request),
        )
        candidates = payload.get("competencies")
        if not isinstance(candidates, list):
            return []

        evidence: list[CompetencyEvidence] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            parsed = parse_llm_candidate(candidate)
            if parsed:
                evidence.append(parsed)
        return evidence


class NormalizationAgent:
    name = "normalizer"

    def normalize(self, evidence: list[CompetencyEvidence]) -> list[CompetencyEvidence]:
        seen: set[tuple[str, str, str]] = set()
        normalized: list[CompetencyEvidence] = []
        for item in evidence:
            key = (item.name, item.source_job_id, item.matched_text)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(item)
        return normalized


class VerificationAgent:
    name = "verifier"

    def verify(
        self,
        evidence: list[CompetencyEvidence],
        min_confidence: float,
    ) -> list[CompetencySummary]:
        grouped: dict[str, list[CompetencyEvidence]] = defaultdict(list)
        for item in evidence:
            if item.confidence >= min_confidence:
                grouped[item.name].append(item)

        summaries: list[CompetencySummary] = []
        for name, items in grouped.items():
            offer_keys: set[str] = set()
            offers: list[CompetencyOfferContext] = []
            for item in items:
                if item.source_job_id in offer_keys:
                    continue
                offer_keys.add(item.source_job_id)
                offers.append(
                    CompetencyOfferContext(
                        source=item.source,
                        source_job_id=item.source_job_id,
                        title=item.title,
                        company_name=item.company_name,
                    )
                )

            confidence = min(0.99, max(item.confidence for item in items) + 0.1 * (len(offers) - 1))
            summaries.append(
                CompetencySummary(
                    name=name,
                    category=items[0].category,
                    evidence_count=len(offers),
                    confidence=round(confidence, 2),
                    offers=offers,
                )
            )

        return sorted(
            summaries,
            key=lambda item: (-item.evidence_count, -item.confidence, item.name),
        )


def extract_competencies_from_offers(
    request: CompetencyExtractionRequest,
    llm_client: JsonLlmClient | None = None,
) -> CompetencyExtractionResponse:
    trace: list[AgentTraceStep] = []

    llm_client = llm_client or build_default_llm_client()
    if llm_client:
        extractor_name = LlmCandidateExtractionAgent.name
        try:
            raw_evidence = LlmCandidateExtractionAgent(llm_client).extract(request)
        except (OSError, TimeoutError, urllib.error.URLError, ValueError):
            extractor_name = CandidateExtractionAgent.name
            raw_evidence = CandidateExtractionAgent().extract(request.offers)
    else:
        extractor_name = CandidateExtractionAgent.name
        raw_evidence = CandidateExtractionAgent().extract(request.offers)

    trace.append(
        AgentTraceStep(
            agent_name=extractor_name,
            status=AgentStatus.PASSED,
            message=f"{len(raw_evidence)} candidates extracted from {len(request.offers)} offers.",
        )
    )

    normalizer = NormalizationAgent()
    normalized_evidence = normalizer.normalize(raw_evidence)
    trace.append(
        AgentTraceStep(
            agent_name=normalizer.name,
            status=AgentStatus.PASSED,
            message=f"{len(normalized_evidence)} normalized evidence items kept.",
        )
    )

    verifier = VerificationAgent()
    competencies = verifier.verify(normalized_evidence, request.min_confidence)
    trace.append(
        AgentTraceStep(
            agent_name=verifier.name,
            status=AgentStatus.PASSED if competencies else AgentStatus.WARNING,
            message=f"{len(competencies)} competencies verified.",
        )
    )

    return CompetencyExtractionResponse(
        run_id=str(uuid4()),
        extracted_at=datetime.now(UTC).isoformat(),
        keyword=request.keyword,
        job_title=request.job_title,
        offer_count=len(request.offers),
        competencies=competencies,
        agent_trace=trace,
    )


class SkillDefinition(BaseModel):
    name: str
    category: CompetencyCategory
    base_confidence: float


SKILL_ALIASES: dict[str, SkillDefinition] = {
    "python": SkillDefinition(
        name="Python", category=CompetencyCategory.TECHNICAL, base_confidence=0.75
    ),
    "sql": SkillDefinition(name="SQL", category=CompetencyCategory.TECHNICAL, base_confidence=0.75),
    "postgresql": SkillDefinition(
        name="PostgreSQL", category=CompetencyCategory.TECHNICAL, base_confidence=0.8
    ),
    "power bi": SkillDefinition(
        name="Power BI", category=CompetencyCategory.TOOL, base_confidence=0.85
    ),
    "powerbi": SkillDefinition(
        name="Power BI", category=CompetencyCategory.TOOL, base_confidence=0.85
    ),
    "machine learning": SkillDefinition(
        name="Machine Learning", category=CompetencyCategory.TECHNICAL, base_confidence=0.8
    ),
    "statistiques": SkillDefinition(
        name="Statistiques", category=CompetencyCategory.METHOD, base_confidence=0.7
    ),
    "etl": SkillDefinition(name="ETL", category=CompetencyCategory.TECHNICAL, base_confidence=0.75),
    "data visualisation": SkillDefinition(
        name="Data Visualisation", category=CompetencyCategory.METHOD, base_confidence=0.7
    ),
    "qualite de donnees": SkillDefinition(
        name="Qualite de donnees", category=CompetencyCategory.METHOD, base_confidence=0.7
    ),
}


def alias_matches(alias: str, normalized_text: str) -> bool:
    normalized_alias = normalize_text(alias)
    return re.search(rf"(^|\W){re.escape(normalized_alias)}($|\W)", normalized_text) is not None


class LocalOpenAiCompatibleClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 45,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw_response = json.loads(response.read().decode("utf-8"))
        return parse_openai_compatible_json_response(raw_response)


def build_default_llm_client() -> JsonLlmClient | None:
    load_environment()
    base_url = os.getenv("LOCAL_LLM_BASE_URL")
    model = os.getenv("LOCAL_LLM_MODEL")
    if not base_url or not model:
        return None
    timeout = int(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "45"))
    return LocalOpenAiCompatibleClient(base_url=base_url, model=model, timeout_seconds=timeout)


def parse_openai_compatible_json_response(payload: dict[str, Any]) -> dict[str, object]:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("Invalid OpenAI-compatible response shape.") from error
    if not isinstance(content, str):
        raise ValueError("OpenAI-compatible response content must be a string.")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON response must be an object.")
    return parsed


def parse_llm_candidate(candidate: dict[str, object]) -> CompetencyEvidence | None:
    try:
        name = str(candidate["name"]).strip()
        category = CompetencyCategory(str(candidate.get("category", CompetencyCategory.TECHNICAL)))
        raw_confidence = candidate.get("confidence", 0.5)
        confidence = float(raw_confidence) if isinstance(raw_confidence, int | float | str) else 0.5
        source_job_id = str(candidate["source_job_id"]).strip()
        title = str(candidate["title"]).strip()
        company_name = str(candidate["company_name"]).strip()
    except (KeyError, TypeError, ValueError):
        return None
    if not name or not source_job_id:
        return None
    return CompetencyEvidence(
        name=name,
        source=str(candidate.get("source") or "France Travail"),
        category=category,
        confidence=max(0, min(1, confidence)),
        source_job_id=source_job_id,
        title=title,
        company_name=company_name,
        matched_text=str(candidate.get("matched_text") or name),
    )


LLM_EXTRACTION_SYSTEM_PROMPT = """
Tu extrais les competences explicites d'offres d'emploi.
Reponds uniquement en JSON avec la cle "competencies".
Chaque competence doit avoir: name, category, confidence, source_job_id, title,
company_name, matched_text.
Categories autorisees: technical, method, tool, domain, language.
N'invente pas de competence absente du texte.
""".strip()


def build_llm_extraction_prompt(request: CompetencyExtractionRequest) -> str:
    offers_payload = [
        {
            "source_job_id": offer.source_job_id,
            "title": offer.title,
            "company_name": offer.company_name,
            "description_text": offer.description_text[:3000],
        }
        for offer in request.offers
    ]
    return json.dumps(
        {
            "keyword": request.keyword,
            "job_title": request.job_title,
            "offers": offers_payload,
        },
        ensure_ascii=False,
    )
