from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from app.competencies import (
    CompetencyExtractionRequest,
    CompetencyExtractionResponse,
    JsonLlmClient,
    extract_competencies_from_offers,
)
from app.jobs import (
    DEFAULT_SEARCH_CONFIG_PATH,
    JobSearchRequest,
    JobSearchResponse,
    JobSourceConnector,
    load_search_request_config,
    search_jobs,
)
from app.storage import build_repository_from_env


class CompetencyAnalysisRepository(Protocol):
    def save_analysis(
        self,
        request: JobSearchRequest,
        job_response: JobSearchResponse,
        competency_response: CompetencyExtractionResponse,
    ) -> str: ...


class CompetencyAnalysisResponse(BaseModel):
    job_search: JobSearchResponse
    competency_extraction: CompetencyExtractionResponse
    persisted: bool
    persistence_id: str | None = None


def analyze_competencies(
    request: JobSearchRequest,
    connectors: list[JobSourceConnector] | None = None,
    repository: CompetencyAnalysisRepository | None = None,
    llm_client: JsonLlmClient | None = None,
) -> CompetencyAnalysisResponse:
    job_response = search_jobs(request, connectors=connectors)
    competency_response = extract_competencies_from_offers(
        CompetencyExtractionRequest(
            keyword=", ".join(request.keywords),
            job_title=request.keywords[0] if request.keywords else None,
            offers=job_response.offers,
        ),
        llm_client=llm_client,
    )

    repository = repository or build_repository_from_env()
    persistence_id = None
    if repository:
        persistence_id = repository.save_analysis(request, job_response, competency_response)

    return CompetencyAnalysisResponse(
        job_search=job_response,
        competency_extraction=competency_response,
        persisted=persistence_id is not None,
        persistence_id=persistence_id,
    )


def analyze_competencies_from_config(
    config_path: Path = DEFAULT_SEARCH_CONFIG_PATH,
    repository: CompetencyAnalysisRepository | None = None,
    llm_client: JsonLlmClient | None = None,
) -> CompetencyAnalysisResponse:
    return analyze_competencies(
        load_search_request_config(config_path),
        repository=repository,
        llm_client=llm_client,
    )
