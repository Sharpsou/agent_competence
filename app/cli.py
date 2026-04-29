from __future__ import annotations

import json

from app.jobs import (
    DEFAULT_SEARCH_CONFIG_PATH,
    build_interactive_search_request,
    save_search_request_config,
    search_jobs,
)


def main() -> None:
    request = build_interactive_search_request()
    save_search_request_config(request)
    response = search_jobs(request)

    print(f"\nConfig mise a jour: {DEFAULT_SEARCH_CONFIG_PATH}")
    print(f"Offres trouvees: {len(response.offers)}\n")
    print(json.dumps(response.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
