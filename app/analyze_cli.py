from __future__ import annotations

import argparse
import json

from app.competency_analysis import analyze_competencies_from_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse les offres de la config et sauvegarde les competences."
    )
    parser.parse_args()

    response = analyze_competencies_from_config()
    print(f"Offres analysees: {len(response.job_search.offers)}")
    print(f"Competences trouvees: {len(response.competency_extraction.competencies)}")
    print(f"Sauvegarde PostgreSQL: {'oui' if response.persisted else 'non'}")
    if response.persistence_id:
        print(f"Run sauvegarde: {response.persistence_id}")
    print(json.dumps(response.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
