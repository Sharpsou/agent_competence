from fastapi import FastAPI

from app.competencies import (
    CompetencyExtractionRequest,
    CompetencyExtractionResponse,
    extract_competencies_from_offers,
)
from app.competency_analysis import (
    CompetencyAnalysisResponse,
    analyze_competencies,
    analyze_competencies_from_config,
)
from app.jobs import JobSearchRequest, JobSearchResponse, search_jobs, search_jobs_from_config

app = FastAPI(title="Agent Competence API", version="0.1.0")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs/search", response_model=JobSearchResponse, tags=["jobs"])
async def search_job_offers(request: JobSearchRequest) -> JobSearchResponse:
    return search_jobs(request)


@app.post("/jobs/search/from-config", response_model=JobSearchResponse, tags=["jobs"])
async def search_job_offers_from_config() -> JobSearchResponse:
    return search_jobs_from_config()


@app.post(
    "/competencies/extract",
    response_model=CompetencyExtractionResponse,
    tags=["competencies"],
)
async def extract_competencies(
    request: CompetencyExtractionRequest,
) -> CompetencyExtractionResponse:
    return extract_competencies_from_offers(request)


@app.post(
    "/competencies/analyze",
    response_model=CompetencyAnalysisResponse,
    tags=["competencies"],
)
async def analyze_competencies_from_request(
    request: JobSearchRequest,
) -> CompetencyAnalysisResponse:
    return analyze_competencies(request)


@app.post(
    "/competencies/analyze/from-config",
    response_model=CompetencyAnalysisResponse,
    tags=["competencies"],
)
async def analyze_competencies_using_config() -> CompetencyAnalysisResponse:
    return analyze_competencies_from_config()
