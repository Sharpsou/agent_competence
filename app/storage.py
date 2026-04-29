from __future__ import annotations

import os
from typing import Any

from app.competencies import CompetencyExtractionResponse
from app.jobs import JobSearchRequest, JobSearchResponse, normalize_text
from app.settings import load_environment


def build_repository_from_env() -> PostgresCompetencyRepository | None:
    load_environment()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    return PostgresCompetencyRepository(database_url)


class PostgresCompetencyRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def save_analysis(
        self,
        request: JobSearchRequest,
        job_response: JobSearchResponse,
        competency_response: CompetencyExtractionResponse,
    ) -> str:
        try:
            import psycopg
            from psycopg.types.json import Jsonb
        except ImportError as error:
            raise RuntimeError(
                "psycopg is required for PostgreSQL persistence. "
                'Install the project with: python -m pip install -e ".[dev]"'
            ) from error

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into job_search_runs (
                      request_keyword,
                      request_job_title,
                      request_payload
                    )
                    values (%s, %s, %s)
                    returning id
                    """,
                    (
                        ", ".join(request.keywords),
                        request.keywords[0] if request.keywords else None,
                        Jsonb(request.model_dump(mode="json")),
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("PostgreSQL did not return a job_search_runs id.")
                run_id = str(row[0])

                offer_ids: dict[tuple[str, str], str] = {}
                company_ids: dict[str, str] = {}
                for offer in job_response.offers:
                    company_id = self._upsert_company(cursor, offer.company_name)
                    company_ids[offer.source_job_id] = company_id
                    offer_id = self._upsert_offer(cursor, offer, company_id, Jsonb)
                    offer_ids[(offer.source, offer.source_job_id)] = offer_id
                    cursor.execute(
                        """
                        insert into job_search_run_offers (run_id, offer_id)
                        values (%s, %s)
                        on conflict (run_id, offer_id) do nothing
                        """,
                        (run_id, offer_id),
                    )

                extractor_name = (
                    competency_response.agent_trace[0].agent_name
                    if competency_response.agent_trace
                    else "unknown"
                )
                verifier_status = (
                    competency_response.agent_trace[-1].status.value
                    if competency_response.agent_trace
                    else "unknown"
                )

                for competency in competency_response.competencies:
                    competency_id = self._upsert_competency(
                        cursor, competency.name, competency.category.value
                    )
                    for offer_context in competency.offers:
                        observation_offer_id = offer_ids.get(
                            (offer_context.source, offer_context.source_job_id)
                        )
                        observation_company_id = company_ids.get(offer_context.source_job_id)
                        if not observation_offer_id:
                            continue
                        cursor.execute(
                            """
                            insert into competency_observations (
                              run_id,
                              offer_id,
                              company_id,
                              competency_id,
                              confidence,
                              matched_text,
                              extractor_name,
                              verifier_status
                            )
                            values (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                run_id,
                                observation_offer_id,
                                observation_company_id,
                                competency_id,
                                competency.confidence,
                                competency.name,
                                extractor_name,
                                verifier_status,
                            ),
                        )
            connection.commit()
        return run_id

    def _upsert_company(self, cursor: Any, company_name: str) -> str:
        cursor.execute(
            """
            insert into companies (name, normalized_name)
            values (%s, %s)
            on conflict (normalized_name)
            do update set name = excluded.name
            returning id
            """,
            (company_name, normalize_text(company_name)),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("PostgreSQL did not return a company id.")
        return str(row[0])

    def _upsert_offer(self, cursor: Any, offer: Any, company_id: str, jsonb: Any) -> str:
        cursor.execute(
            """
            insert into job_offers (
              source,
              source_job_id,
              company_id,
              title,
              normalized_title,
              location_text,
              remote_mode,
              contract_type,
              description_text,
              published_at,
              detail_url,
              raw_payload
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (source, source_job_id)
            do update set
              company_id = excluded.company_id,
              title = excluded.title,
              normalized_title = excluded.normalized_title,
              location_text = excluded.location_text,
              remote_mode = excluded.remote_mode,
              contract_type = excluded.contract_type,
              description_text = excluded.description_text,
              published_at = excluded.published_at,
              detail_url = excluded.detail_url,
              raw_payload = excluded.raw_payload
            returning id
            """,
            (
                offer.source,
                offer.source_job_id,
                company_id,
                offer.title,
                normalize_text(offer.title),
                offer.location_text,
                offer.remote_mode.value,
                offer.contract_type,
                offer.description_text,
                offer.published_at,
                offer.detail_url,
                jsonb(offer.raw_payload) if offer.raw_payload else None,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("PostgreSQL did not return a job offer id.")
        return str(row[0])

    def _upsert_competency(self, cursor: Any, name: str, category: str) -> str:
        cursor.execute(
            """
            insert into competencies (name, normalized_name, category)
            values (%s, %s, %s)
            on conflict (normalized_name)
            do update set
              name = excluded.name,
              category = excluded.category
            returning id
            """,
            (name, normalize_text(name), category),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("PostgreSQL did not return a competency id.")
        return str(row[0])
