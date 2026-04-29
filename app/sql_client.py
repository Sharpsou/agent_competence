from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from typing import Any

from app.settings import load_environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Petit client SQL PostgreSQL du projet.")
    parser.add_argument("-q", "--query", help="Requete SQL a executer.")
    args = parser.parse_args()

    load_environment()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL doit etre renseigne.")

    if args.query:
        execute_query(database_url, args.query)
        return

    print("Client SQL Agent Competence. Tape `exit` pour quitter.")
    while True:
        query = input("sql> ").strip()
        if query.lower() in {"exit", "quit", "\\q"}:
            return
        if not query:
            continue
        execute_query(database_url, query)


def execute_query(database_url: str, query: str) -> None:
    try:
        import psycopg
    except ImportError as error:
        raise SystemExit('psycopg est requis. Lance: python -m pip install -e ".[dev]"') from error

    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(query)
        if cursor.description:
            rows = cursor.fetchall()
            headers = [column.name for column in cursor.description]
            print_table(headers, rows)
        else:
            connection.commit()
            print(f"{cursor.rowcount} ligne(s) affectee(s).")


def print_table(headers: list[str], rows: Sequence[Sequence[Any]]) -> None:
    values = [[stringify(value) for value in row] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in values)) if values else len(header)
        for index, header in enumerate(headers)
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in values:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def stringify(value: object) -> str:
    if value is None:
        return ""
    return str(value)


if __name__ == "__main__":
    main()
