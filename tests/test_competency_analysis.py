from app.competency_analysis import analyze_competencies
from app.jobs import JobOffer, JobSearchRequest, RemoteMode


class FakeConnector:
    source_name = "Fake"

    def fetch_jobs(self, request: JobSearchRequest) -> list[JobOffer]:
        return [
            JobOffer(
                source="Fake",
                source_job_id="1",
                title="Data Analyst",
                company_name="Acme",
                location_text="Nantes",
                remote_mode=RemoteMode.HYBRID,
                contract_type="CDI",
                description_text="SQL, Python et Power BI.",
                published_at="2026-04-29",
            )
        ]


class FakeRepository:
    def __init__(self) -> None:
        self.saved = False

    def save_analysis(self, request, job_response, competency_response) -> str:
        assert request.keywords == ["data"]
        assert job_response.offers[0].source_job_id == "1"
        assert competency_response.competencies
        self.saved = True
        return "run-1"


def test_analyze_competencies_searches_extracts_and_persists() -> None:
    repository = FakeRepository()

    response = analyze_competencies(
        JobSearchRequest(keywords=["data"], locations=["Nantes"]),
        connectors=[FakeConnector()],
        repository=repository,
    )

    assert repository.saved is True
    assert response.persisted is True
    assert response.persistence_id == "run-1"
    assert response.job_search.offers
    assert [competency.name for competency in response.competency_extraction.competencies] == [
        "Power BI",
        "Python",
        "SQL",
    ]
