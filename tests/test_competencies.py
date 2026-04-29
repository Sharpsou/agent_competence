from fastapi.testclient import TestClient

from app.competencies import (
    CompetencyExtractionRequest,
    JsonLlmClient,
    extract_competencies_from_offers,
)
from app.jobs import JobOffer, RemoteMode
from app.main import app


def test_extracts_and_verifies_competencies_from_job_offers() -> None:
    offers = [
        job_offer(
            "1",
            "Data Analyst",
            "Acme",
            "SQL, Python, Power BI. Maitrise de la data visualisation.",
        ),
        job_offer(
            "2",
            "Data Scientist",
            "Beta",
            "Python, machine learning, SQL et statistiques.",
        ),
    ]

    response = extract_competencies_from_offers(
        CompetencyExtractionRequest(
            keyword="data",
            job_title="Data Analyst",
            offers=offers,
        )
    )

    names = [competency.name for competency in response.competencies]

    assert names[:3] == ["Python", "SQL", "Power BI"]
    assert response.competencies[0].evidence_count == 2
    assert response.competencies[0].confidence >= 0.8
    assert all(step.status == "passed" for step in response.agent_trace)


def test_extraction_keeps_offer_company_and_title_context() -> None:
    response = extract_competencies_from_offers(
        CompetencyExtractionRequest(
            keyword="sql",
            offers=[
                job_offer(
                    "1",
                    "Developpeur SQL",
                    "DataCorp",
                    "PostgreSQL, SQL, ETL et qualite de donnees.",
                )
            ],
        )
    )

    sql = next(competency for competency in response.competencies if competency.name == "SQL")

    assert sql.offers[0].source_job_id == "1"
    assert sql.offers[0].title == "Developpeur SQL"
    assert sql.offers[0].company_name == "DataCorp"


def test_competencies_endpoint_accepts_offers_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/competencies/extract",
        json={
            "keyword": "data",
            "offers": [
                {
                    "source": "Fake",
                    "source_job_id": "1",
                    "title": "Data Analyst",
                    "company_name": "Acme",
                    "location_text": "Nantes",
                    "remote_mode": "hybrid",
                    "contract_type": "CDI",
                    "description_text": "SQL, Python et Power BI.",
                    "published_at": "2026-04-29",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [competency["name"] for competency in payload["competencies"]] == [
        "Power BI",
        "Python",
        "SQL",
    ]


def test_extraction_uses_llm_agent_when_available() -> None:
    class FakeLlmClient:
        def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
            assert "competences" in system_prompt.lower()
            assert "Data Analyst" in user_prompt
            return {
                "competencies": [
                    {
                        "name": "dbt",
                        "category": "tool",
                        "confidence": 0.86,
                        "source_job_id": "1",
                        "title": "Data Analyst",
                        "company_name": "Acme",
                        "matched_text": "dbt",
                    }
                ]
            }

    offers = [job_offer("1", "Data Analyst", "Acme", "dbt, SQL et modelisation data.")]

    response = extract_competencies_from_offers(
        CompetencyExtractionRequest(keyword="data", offers=offers),
        llm_client=FakeLlmClient(),
    )

    assert isinstance(FakeLlmClient(), JsonLlmClient)
    assert response.competencies[0].name == "dbt"
    assert response.agent_trace[0].agent_name == "llm_candidate_extractor"


def test_extraction_falls_back_when_local_llm_is_stopped() -> None:
    class StoppedLlmClient:
        def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
            raise OSError("local server stopped")

    response = extract_competencies_from_offers(
        CompetencyExtractionRequest(
            keyword="data",
            offers=[job_offer("1", "Data Analyst", "Acme", "SQL et Python.")],
        ),
        llm_client=StoppedLlmClient(),
    )

    assert response.agent_trace[0].agent_name == "candidate_extractor"
    assert [competency.name for competency in response.competencies] == ["Python", "SQL"]


def job_offer(source_job_id: str, title: str, company: str, description: str) -> JobOffer:
    return JobOffer(
        source="Fake",
        source_job_id=source_job_id,
        title=title,
        company_name=company,
        location_text="France",
        remote_mode=RemoteMode.HYBRID,
        contract_type="CDI",
        description_text=description,
        published_at="2026-04-29",
    )
