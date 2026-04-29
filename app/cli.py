from __future__ import annotations

import json

from app.jobs import (
    DEFAULT_SEARCH_CONFIG_PATH,
    ask_yes_no,
    build_interactive_search_request,
    clear_http_cache,
    load_search_request_config,
    save_search_request_config,
    search_jobs,
)


def main() -> None:
    use_existing_cache = ask_yes_no(
        input,
        prompt="Utiliser la derniere config et le cache deja trouve ?",
    )
    if use_existing_cache:
        request = load_search_request_config()
    else:
        clear_http_cache()
        print("Cache HTTP supprime avant la recherche.")
        request = build_interactive_search_request()
        save_search_request_config(request)

    response = search_jobs(request)

    print(f"\nConfig utilisee: {DEFAULT_SEARCH_CONFIG_PATH}")
    print(f"Offres trouvees: {len(response.offers)}\n")
    print(json.dumps(response.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
