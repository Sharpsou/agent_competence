from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.jobs import (
    DEFAULT_SEARCH_CONFIG_PATH,
    FranceTravailConnector,
    JobOffer,
    JobSearchRequest,
    RemoteMode,
    build_interactive_search_request,
    detect_remote_mode,
    extract_job_posting,
    load_search_request_config,
    resolve_location_code,
    save_search_request_config,
    search_jobs,
    search_jobs_from_config,
)
from app.main import app


class FakeConnector:
    source_name = "Fake"

    def fetch_jobs(self, request: JobSearchRequest) -> list[JobOffer]:
        return [
            JobOffer(
                source="Fake",
                source_job_id="1",
                title="Data Analyst CDI",
                company_name="Example",
                location_text="Nantes",
                remote_mode=RemoteMode.HYBRID,
                contract_type="CDI",
                description_text="SQL Python teletravail",
                published_at="2026-04-29",
                detail_url="https://example.test/jobs/1",
            ),
            JobOffer(
                source="Fake",
                source_job_id="2",
                title="Consultant SAP",
                company_name="Example",
                location_text="Paris",
                remote_mode=RemoteMode.ONSITE,
                contract_type="CDI",
                description_text="SAP ERP",
                published_at="2026-04-29",
            ),
        ]


def test_resolves_known_city_codes() -> None:
    assert resolve_location_code("Nantes") == "44109"
    assert resolve_location_code("Saint-Nazaire") == "44184"
    assert resolve_location_code("Paris") == "75056"
    assert resolve_location_code("Ville inconnue") is None


def test_detects_remote_mode() -> None:
    assert detect_remote_mode("Poste full remote en France") == RemoteMode.REMOTE
    assert detect_remote_mode("2 jours de teletravail par semaine") == RemoteMode.HYBRID
    assert detect_remote_mode("Poste sur site") == RemoteMode.ONSITE


def test_builds_france_travail_search_url_with_filters() -> None:
    request = JobSearchRequest(
        keywords=["Data Analyst"],
        location="Nantes",
        location_code="44109",
        radius_km=15,
    )

    url = FranceTravailConnector().build_search_url("Data Analyst", request)

    assert "motsCles=Data+Analyst" in url
    assert "lieux=44109" in url
    assert "rayon=15" in url
    assert "tri=0" in url


def test_extracts_france_travail_microdata_job_posting() -> None:
    html = """
    <div itemtype="http://schema.org/JobPosting" itemscope>
      <span itemprop="identifier" content="123ABC"></span>
      <h1 itemprop="title">Data Analyst</h1>
      <div itemprop="hiringOrganization" itemscope>
        <span itemprop="name">Example Corp</span>
      </div>
      <div itemprop="jobLocation" itemscope>
        <div itemprop="address" itemscope>
          <span itemprop="addressLocality">Nantes</span>
          <span itemprop="addressRegion">Pays de la Loire</span>
          <span itemprop="addressCountry">France</span>
        </div>
      </div>
      <span itemprop="employmentType">CDI</span>
      <time itemprop="datePosted" content="2026-04-29"></time>
      <div itemprop="description">Poste hybride avec SQL et Python.</div>
    </div>
    """

    posting = extract_job_posting(html)

    assert posting is not None
    assert posting["identifier"]["value"] == "123ABC"
    assert posting["title"] == "Data Analyst"
    assert posting["hiringOrganization"]["name"] == "Example Corp"
    assert posting["jobLocation"]["address"]["addressLocality"] == "Nantes"


def test_search_jobs_filters_results() -> None:
    request = JobSearchRequest(
        keywords=["data"],
        location="Nantes",
        contract_type="CDI",
        remote_mode=RemoteMode.HYBRID,
        excluded_keywords=["SAP"],
    )

    response = search_jobs(request, connectors=[FakeConnector()])

    assert response.resolved_location_code == "44109"
    assert [offer.source_job_id for offer in response.offers] == ["1"]


def test_loads_search_request_from_json_config() -> None:
    request = load_search_request_config(DEFAULT_SEARCH_CONFIG_PATH)

    assert request.keywords
    assert request.locations
    assert request.location
    assert request.contract_type == "CDI"


def test_search_jobs_from_config_uses_json_config() -> None:
    response = search_jobs_from_config(connectors=[FakeConnector()])

    assert response.resolved_location_code == "44109"
    assert response.offers


def test_jobs_search_endpoint_accepts_request_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/jobs/search",
        json={
            "keywords": ["Data Analyst"],
            "location": "Nantes",
            "max_results": 1,
            "sources": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resolved_location_code"] == "44109"
    assert payload["offers"] == []


def test_builds_interactive_search_request_from_prompts() -> None:
    answers = iter(
        ["Data Analyst, Python", "Nantes, Saint-Nazaire", "CDI", "hybrid", "15", "30", "SAP"]
    )

    request = build_interactive_search_request(input_func=lambda _: next(answers))

    assert request.keywords == ["Data Analyst", "Python"]
    assert request.locations == ["Nantes", "Saint-Nazaire"]
    assert request.location == "Nantes"
    assert request.contract_type == "CDI"
    assert request.remote_mode == RemoteMode.HYBRID
    assert request.radius_km == 15
    assert request.max_results == 30
    assert request.excluded_keywords == ["SAP"]


def test_saves_search_request_config() -> None:
    path = Path("data") / "runtime" / f"job-search-request-{uuid4()}.json"
    request = JobSearchRequest(keywords=["Data"], locations=["Nantes"], contract_type="CDI")

    try:
        save_search_request_config(request, path)
        loaded = load_search_request_config(path)

        assert loaded.keywords == ["Data"]
        assert loaded.locations == ["Nantes"]
        assert loaded.contract_type == "CDI"
    finally:
        path.unlink(missing_ok=True)
