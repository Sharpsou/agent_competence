from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from enum import StrEnum
from html import unescape
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

RUNTIME_DIR = Path("data") / "runtime"
HTTP_CACHE_DIR = RUNTIME_DIR / "http-cache"
DEFAULT_SEARCH_CONFIG_PATH = Path("config") / "job_search_request.json"

CITY_CODES = {
    "france": "99100",
    "nantes": "44109",
    "saint-nazaire": "44184",
    "saint nazaire": "44184",
    "paris": "75056",
    "lyon": "69123",
    "marseille": "13055",
    "bordeaux": "33063",
    "toulouse": "31555",
    "lille": "59350",
    "rennes": "35238",
    "strasbourg": "67482",
    "montpellier": "34172",
    "nice": "06088",
}

REMOTE_ONLY_MARKERS = {
    "100% teletravail",
    "full remote",
    "fully remote",
    "entierement a distance",
    "teletravail complet",
}
HYBRID_MARKERS = {
    "teletravail",
    "hybride",
    "hybrid",
    "travail a distance",
    "remote partiel",
}


class RemoteMode(StrEnum):
    ANY = "any"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class JobSource(StrEnum):
    FRANCE_TRAVAIL = "france_travail"


class JobSearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1, description="Mots-cles ou intitules de poste.")
    locations: list[str] = Field(default_factory=list, description="Villes ou zones de recherche.")
    location: str | None = Field(
        default=None,
        description="Ville ou zone principale. Conserve la compatibilite avec les premiers appels.",
    )
    location_code: str | None = Field(default=None, description="Code commune/source si connu.")
    radius_km: int = Field(default=10, ge=0, le=100)
    contract_type: str | None = None
    remote_mode: RemoteMode = RemoteMode.ANY
    sources: list[JobSource] = Field(default_factory=lambda: [JobSource.FRANCE_TRAVAIL])
    max_results: int = Field(default=20, ge=1, le=100)
    excluded_keywords: list[str] = Field(default_factory=list)
    include_raw_payload: bool = False

    @field_validator("keywords", "excluded_keywords", mode="before")
    @classmethod
    def split_string_values(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("locations", mode="before")
    @classmethod
    def split_locations(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class JobOffer(BaseModel):
    source: str
    source_job_id: str
    title: str
    company_name: str
    location_text: str
    remote_mode: RemoteMode
    contract_type: str
    description_text: str
    published_at: str
    detail_url: str | None = None
    raw_payload: dict[str, Any] | None = None


class JobSearchResponse(BaseModel):
    request_id: str
    stored_at: str
    resolved_location_code: str | None
    offers: list[JobOffer]


class JobSourceConnector(Protocol):
    source_name: str

    def fetch_jobs(self, request: JobSearchRequest) -> list[JobOffer]: ...


def search_jobs(
    request: JobSearchRequest,
    connectors: list[JobSourceConnector] | None = None,
) -> JobSearchResponse:
    request_id = str(uuid4())
    stored_at = datetime.now(UTC).isoformat()
    resolved_location_code = resolve_location_code(primary_location(request), request.location_code)
    effective_request = request.model_copy(update={"location_code": resolved_location_code})

    active_connectors = connectors or build_connectors(effective_request)
    offers: list[JobOffer] = []
    seen: set[tuple[str, str]] = set()

    for connector in active_connectors:
        for offer in connector.fetch_jobs(effective_request):
            key = (offer.source, offer.source_job_id)
            if key in seen or not offer_matches_request(offer, effective_request):
                continue
            seen.add(key)
            offers.append(offer)
            if len(offers) >= effective_request.max_results:
                return JobSearchResponse(
                    request_id=request_id,
                    stored_at=stored_at,
                    resolved_location_code=resolved_location_code,
                    offers=offers,
                )

    return JobSearchResponse(
        request_id=request_id,
        stored_at=stored_at,
        resolved_location_code=resolved_location_code,
        offers=offers,
    )


def search_jobs_from_config(
    config_path: Path = DEFAULT_SEARCH_CONFIG_PATH,
    connectors: list[JobSourceConnector] | None = None,
) -> JobSearchResponse:
    return search_jobs(load_search_request_config(config_path), connectors=connectors)


def build_connectors(request: JobSearchRequest) -> list[JobSourceConnector]:
    connectors: list[JobSourceConnector] = []
    if JobSource.FRANCE_TRAVAIL in request.sources:
        connectors.append(FranceTravailConnector())
    return connectors


def load_search_request_config(config_path: Path = DEFAULT_SEARCH_CONFIG_PATH) -> JobSearchRequest:
    with config_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    return JobSearchRequest.model_validate(payload)


def save_search_request_config(
    request: JobSearchRequest,
    config_path: Path = DEFAULT_SEARCH_CONFIG_PATH,
) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(request.model_dump(mode="json"), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def primary_location(request: JobSearchRequest) -> str | None:
    if request.location:
        return request.location
    if request.locations:
        return request.locations[0]
    return None


def build_interactive_search_request(input_func: Any = input) -> JobSearchRequest:
    keywords = ask_list(input_func, "Mots-cles / postes (separes par des virgules)")
    locations = ask_list(input_func, "Ville(s) (separees par des virgules)")
    contract_type = ask_optional(input_func, "Type de contrat (CDI, CDD, alternance...)")
    remote_mode = ask_remote_mode(input_func)
    radius_km = ask_int(input_func, "Rayon en km", default=10, minimum=0, maximum=100)
    max_results = ask_int(input_func, "Nombre max d'offres", default=20, minimum=1, maximum=100)
    excluded_keywords = ask_list(input_func, "Mots a exclure (optionnel)", required=False)

    return JobSearchRequest(
        keywords=keywords,
        locations=locations,
        location=locations[0] if locations else None,
        radius_km=radius_km,
        contract_type=contract_type,
        remote_mode=remote_mode,
        max_results=max_results,
        excluded_keywords=excluded_keywords,
    )


def ask_yes_no(
    input_func: Any,
    prompt: str = "Utiliser le cache deja trouve ?",
    default: bool = True,
) -> bool:
    suffix = "O/n" if default else "o/N"
    while True:
        raw_value = input_func(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw_value:
            return default
        if raw_value in {"o", "oui", "y", "yes"}:
            return True
        if raw_value in {"n", "non", "no"}:
            return False
        print("Veuillez repondre par oui ou non.")


def clear_http_cache(cache_dir: Path = HTTP_CACHE_DIR) -> None:
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


def ask_list(input_func: Any, prompt: str, required: bool = True) -> list[str]:
    while True:
        raw_value = input_func(f"{prompt}: ").strip()
        values = [item.strip() for item in raw_value.split(",") if item.strip()]
        if values or not required:
            return values
        print("Veuillez renseigner au moins une valeur.")


def ask_optional(input_func: Any, prompt: str) -> str | None:
    value = input_func(f"{prompt}: ").strip()
    return value or None


def ask_int(
    input_func: Any,
    prompt: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    while True:
        raw_value = input_func(f"{prompt} [{default}]: ").strip()
        if not raw_value:
            return default
        try:
            value = int(raw_value)
        except ValueError:
            print("Veuillez saisir un nombre entier.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Veuillez saisir une valeur entre {minimum} et {maximum}.")


def ask_remote_mode(input_func: Any) -> RemoteMode:
    allowed = ", ".join(mode.value for mode in RemoteMode)
    while True:
        raw_value = input_func(f"Teletravail ({allowed}) [any]: ").strip().lower()
        if not raw_value:
            return RemoteMode.ANY
        try:
            return RemoteMode(raw_value)
        except ValueError:
            print(f"Valeur invalide. Choix possibles: {allowed}.")


def resolve_location_code(location: str | None, explicit_code: str | None = None) -> str | None:
    if explicit_code:
        return explicit_code.strip()
    if not location:
        return None
    return CITY_CODES.get(normalize_text(location))


def offer_matches_request(offer: JobOffer, request: JobSearchRequest) -> bool:
    haystack = normalize_text(" ".join([offer.title, offer.description_text, offer.contract_type]))

    if request.contract_type and normalize_text(request.contract_type) not in haystack:
        return False
    if request.remote_mode != RemoteMode.ANY and offer.remote_mode != request.remote_mode:
        return False
    return not any(normalize_text(keyword) in haystack for keyword in request.excluded_keywords)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", normalized.lower().replace("'", " ")).strip()


def detect_remote_mode(description_text: str) -> RemoteMode:
    lowered = normalize_text(description_text)
    if any(marker in lowered for marker in REMOTE_ONLY_MARKERS):
        return RemoteMode.REMOTE
    if any(marker in lowered for marker in HYBRID_MARKERS):
        return RemoteMode.HYBRID
    return RemoteMode.ONSITE


class FranceTravailConnector:
    source_name = "France Travail"
    search_url = "https://candidat.francetravail.fr/offres/recherche"
    base_url = "https://candidat.francetravail.fr"

    def __init__(self, fetcher: PublicWebFetcher | None = None) -> None:
        self.fetcher = fetcher or PublicWebFetcher(source_name=self.source_name)

    def fetch_jobs(self, request: JobSearchRequest) -> list[JobOffer]:
        offers: list[JobOffer] = []
        seen: set[str] = set()
        max_per_keyword = max(1, request.max_results)

        for keyword in request.keywords:
            search_html = self.fetcher.fetch_text(self.build_search_url(keyword, request))
            detail_urls = extract_item_list_urls(search_html)
            if not detail_urls:
                detail_urls = extract_links_by_pattern(
                    search_html,
                    r'href=["\'](/offres/recherche/detail/[^"\']+)["\']',
                    self.base_url,
                )

            for detail_url in detail_urls[:max_per_keyword]:
                offer = self.fetch_detail(detail_url, keyword, request.include_raw_payload)
                if not offer or offer.source_job_id in seen:
                    continue
                seen.add(offer.source_job_id)
                offers.append(offer)

        return offers

    def build_search_url(self, keyword: str, request: JobSearchRequest) -> str:
        params = {
            "motsCles": keyword,
            "offresPartenaires": "true",
            "rayon": str(request.radius_km),
            "tri": "0",
        }
        if request.location_code:
            params["lieux"] = request.location_code
        return f"{self.search_url}?{urllib.parse.urlencode(params)}"

    def fetch_detail(
        self, detail_url: str, keyword: str, include_raw_payload: bool = False
    ) -> JobOffer | None:
        full_url = absolute_url(self.base_url, detail_url)
        html = self.fetcher.fetch_text(full_url)
        posting = extract_job_posting(html)
        if not posting:
            return None

        source_job_id = extract_source_job_id(posting, detail_url)
        title = str(posting.get("title") or keyword)
        description_text = strip_html(str(posting.get("description") or ""))

        return JobOffer(
            source=self.source_name,
            source_job_id=source_job_id,
            title=title,
            company_name=extract_company_name(posting),
            location_text=extract_location_text(posting),
            remote_mode=detect_remote_mode(description_text),
            contract_type=extract_contract_type(posting, html),
            description_text=description_text,
            published_at=str(posting.get("datePosted") or "")[:10],
            detail_url=full_url,
            raw_payload={"job_posting": posting} if include_raw_payload else None,
        )


class PublicWebFetcher:
    def __init__(
        self,
        source_name: str,
        cache_dir: Path = HTTP_CACHE_DIR,
        timeout_seconds: int = 20,
        delay_seconds: float = 2.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self.cache_dir = cache_dir / source_name.lower().replace(" ", "-")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_at = 0.0

    def fetch_text(self, url: str) -> str:
        cache_path = self._cache_path(url)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AgentCompetenceBot/0.1)",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            content: str = response.read().decode("utf-8", errors="replace")

        self._last_request_at = time.monotonic()
        cache_path.write_text(content, encoding="utf-8")
        return content

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.html"


def extract_ld_json_objects(html: str) -> list[Any]:
    objects: list[Any] = []
    matches = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for raw_payload in matches:
        try:
            objects.append(json.loads(raw_payload.strip()))
        except json.JSONDecodeError:
            continue
    return objects


def iter_ld_json_objects(payload: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        objects.append(payload)
        graph = payload.get("@graph")
        if isinstance(graph, list):
            objects.extend(item for item in graph if isinstance(item, dict))
    elif isinstance(payload, list):
        for item in payload:
            objects.extend(iter_ld_json_objects(item))
    return objects


def extract_item_list_urls(html: str) -> list[str]:
    urls: list[str] = []
    for payload in extract_ld_json_objects(html):
        for item in iter_ld_json_objects(payload):
            if item.get("@type") != "ItemList":
                continue
            elements = item.get("itemListElement", [])
            if not isinstance(elements, list):
                continue
            for element in elements:
                if not isinstance(element, dict):
                    continue
                url = element.get("url")
                item_value = element.get("item")
                if isinstance(url, str):
                    urls.append(url)
                elif isinstance(item_value, dict):
                    item_url = item_value.get("url")
                    if isinstance(item_url, str):
                        urls.append(item_url)
    return list(dict.fromkeys(urls))


def extract_links_by_pattern(html: str, pattern: str, base_url: str) -> list[str]:
    matches = re.findall(pattern, html, flags=re.IGNORECASE)
    return list(dict.fromkeys(absolute_url(base_url, match) for match in matches))


def extract_job_posting(html: str) -> dict[str, Any] | None:
    for payload in extract_ld_json_objects(html):
        for item in iter_ld_json_objects(payload):
            if item.get("@type") == "JobPosting":
                return item
    return extract_job_posting_microdata(html)


def extract_job_posting_microdata(html: str) -> dict[str, Any] | None:
    if 'itemtype="http://schema.org/JobPosting"' not in html and (
        "itemtype='http://schema.org/JobPosting'" not in html
    ):
        return None

    posting: dict[str, Any] = {}

    identifier = extract_identifier_value(html)
    if identifier:
        posting["identifier"] = {"value": identifier}

    title = extract_itemprop_html(html, "title")
    if title:
        posting["title"] = strip_html(title)

    description = extract_itemprop_html(html, "description")
    if description:
        posting["description"] = description

    date_posted = extract_itemprop_content(html, "datePosted")
    if date_posted:
        posting["datePosted"] = date_posted

    employment_type = extract_itemprop_content(html, "employmentType")
    if employment_type:
        posting["employmentType"] = employment_type

    company_name = extract_hiring_organization_name(html)
    if company_name:
        posting["hiringOrganization"] = {"name": company_name}

    location = extract_job_location(html)
    if location:
        posting["jobLocation"] = location

    skills = extract_itemprop_list(html, "skills")
    if skills:
        posting["skills"] = skills

    return posting if posting else None


def extract_source_job_id(posting: dict[str, Any], detail_url: str) -> str:
    identifier = posting.get("identifier")
    if isinstance(identifier, dict):
        value = identifier.get("value") or identifier.get("name")
        if value:
            return str(value)
    return detail_url.rstrip("/").rsplit("/", 1)[-1]


def extract_company_name(posting: dict[str, Any]) -> str:
    organization = posting.get("hiringOrganization")
    if isinstance(organization, dict):
        return str(organization.get("name") or "Entreprise non precisee")
    return "Entreprise non precisee"


def extract_itemprop_content(html: str, itemprop: str) -> str | None:
    patterns = [
        rf'itemprop=["\']{re.escape(itemprop)}["\'][^>]*content=["\']([^"\']+)["\']',
        rf'content=["\']([^"\']+)["\'][^>]*itemprop=["\']{re.escape(itemprop)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return unescape(match.group(1)).strip()

    inline_value = extract_itemprop_html(html, itemprop)
    if inline_value:
        return strip_html(inline_value)
    return None


def extract_identifier_value(html: str) -> str | None:
    identifier_block = extract_itemprop_html(html, "identifier")
    if identifier_block:
        value = extract_itemprop_content(identifier_block, "value")
        if value:
            return value

    identifier_content = extract_itemprop_content(html, "identifier")
    if identifier_content:
        return identifier_content

    return extract_itemprop_content(html, "value")


def extract_itemprop_html(html: str, itemprop: str) -> str | None:
    match = re.search(
        rf'<(?P<tag>[a-z0-9]+)[^>]*itemprop=["\']{re.escape(itemprop)}["\'][^>]*>'
        rf"(?P<content>.*?)</(?P=tag)>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return match.group("content").strip()


def extract_itemprop_list(html: str, itemprop: str) -> list[str]:
    matches = re.findall(
        rf'<[^>]*itemprop=["\']{re.escape(itemprop)}["\'][^>]*>(.*?)</[^>]+>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    values = [strip_html(match) for match in matches]
    return [value for value in values if value]


def extract_hiring_organization_name(html: str) -> str | None:
    patterns = [
        r'itemprop=["\']hiringOrganization["\'][^>]*>.*?'
        r'itemprop=["\']name["\'][^>]*content=["\']([^"\']*)["\']',
        r'itemprop=["\']hiringOrganization["\'][^>]*>.*?'
        r'content=["\']([^"\']*)["\'][^>]*itemprop=["\']name["\']',
        r'itemprop=["\']hiringOrganization["\'][^>]*>.*?'
        r'itemprop=["\']name["\'][^>]*>(.*?)</[^>]+>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = strip_html(unescape(match.group(1)))
            if value:
                return value
    return None


def extract_job_location(html: str) -> dict[str, Any] | None:
    locality = extract_itemprop_content(html, "addressLocality")
    region = extract_itemprop_content(html, "addressRegion")
    country = extract_itemprop_content(html, "addressCountry")
    postal_code = extract_itemprop_content(html, "postalCode")

    address = {
        "addressLocality": locality or "",
        "addressRegion": region or "",
        "addressCountry": country or "",
        "postalCode": postal_code or "",
    }
    if not any(address.values()):
        return None
    return {"address": address}


def extract_location_text(posting: dict[str, Any]) -> str:
    location = posting.get("jobLocation")
    if isinstance(location, list) and location:
        location = location[0]
    if isinstance(location, dict):
        address = location.get("address")
        if isinstance(address, dict):
            parts = [
                str(address.get("addressLocality") or "").strip(),
                str(address.get("addressRegion") or "").strip(),
                str(address.get("addressCountry") or "").strip(),
            ]
            parts = [part for part in parts if part]
            if parts:
                return ", ".join(parts)
    return "France"


def extract_contract_type(posting: dict[str, Any], html: str) -> str:
    match = re.search(
        r'<dt><span title="Type de contrat".*?</dt><dd>\s*(.*?)\s*</dd>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        value = strip_html(match.group(1))
        if value:
            return value

    employment_type = posting.get("employmentType")
    if isinstance(employment_type, list):
        return ", ".join(str(item) for item in employment_type if str(item).strip()) or "NC"
    return str(employment_type or "NC")


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def absolute_url(base_url: str, maybe_relative_url: str) -> str:
    return urllib.parse.urljoin(base_url, maybe_relative_url)
