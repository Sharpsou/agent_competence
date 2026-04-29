from fastapi import FastAPI

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
