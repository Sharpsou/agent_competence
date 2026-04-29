from app import cli
from app.jobs import JobSearchRequest, JobSearchResponse


def test_cli_uses_existing_config_without_prompting_filters_when_cache_is_kept(
    monkeypatch,
) -> None:
    config_request = JobSearchRequest(keywords=["Data"], locations=["Nantes"])

    def fake_ask_yes_no(input_func: object, prompt: str = "", default: bool = True) -> bool:
        return True

    def fake_search_jobs(request: JobSearchRequest) -> JobSearchResponse:
        assert request == config_request
        return JobSearchResponse(
            request_id="test",
            stored_at="2026-04-29T00:00:00+00:00",
            resolved_location_code="44109",
            offers=[],
        )

    monkeypatch.setattr(cli, "ask_yes_no", fake_ask_yes_no)
    monkeypatch.setattr(cli, "load_search_request_config", lambda: config_request)
    monkeypatch.setattr(
        cli,
        "build_interactive_search_request",
        lambda: (_ for _ in ()).throw(AssertionError("filters should not be prompted")),
    )
    monkeypatch.setattr(cli, "search_jobs", fake_search_jobs)

    cli.main()


def test_cli_clears_cache_and_prompts_filters_when_cache_is_not_kept(monkeypatch) -> None:
    state = {"cache_cleared": False}
    prompted_request = JobSearchRequest(keywords=["Python"], locations=["Rennes"])

    def fake_ask_yes_no(input_func: object, prompt: str = "", default: bool = True) -> bool:
        return False

    def fake_clear_http_cache() -> None:
        state["cache_cleared"] = True

    def fake_build_interactive_search_request() -> JobSearchRequest:
        assert state["cache_cleared"] is True
        return prompted_request

    def fake_search_jobs(request: JobSearchRequest) -> JobSearchResponse:
        assert request == prompted_request
        return JobSearchResponse(
            request_id="test",
            stored_at="2026-04-29T00:00:00+00:00",
            resolved_location_code="35238",
            offers=[],
        )

    monkeypatch.setattr(cli, "ask_yes_no", fake_ask_yes_no)
    monkeypatch.setattr(cli, "clear_http_cache", fake_clear_http_cache)
    monkeypatch.setattr(
        cli, "build_interactive_search_request", fake_build_interactive_search_request
    )
    monkeypatch.setattr(cli, "save_search_request_config", lambda request: None)
    monkeypatch.setattr(cli, "search_jobs", fake_search_jobs)

    cli.main()
