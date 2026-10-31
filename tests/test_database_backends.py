import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import db  # noqa: E402


def test_postgres_query_portierung():
    assert db._postgres_sql("SELECT * FROM benutzer WHERE email = ? COLLATE NOCASE AND rolle <> ?") == \
        "SELECT * FROM benutzer WHERE LOWER(email) = LOWER(%s) AND rolle <> %s"
    assert db._postgres_sql("SELECT * FROM benutzer WHERE id IS NOT ?") == \
        "SELECT * FROM benutzer WHERE id IS DISTINCT FROM %s"
    assert db._postgres_sql("SELECT * FROM vorauszahlung WHERE mv_id IS ?") == \
        "SELECT * FROM vorauszahlung WHERE mv_id IS NOT DISTINCT FROM %s"
    assert db._postgres_sql("ORDER BY name COLLATE NATUERLICH") == "ORDER BY name"
    assert db._postgres_sql("SELECT * FROM immobilie WHERE id = :i", named=True) == \
        "SELECT * FROM immobilie WHERE id = %(i)s"


def test_postgres_migration_portierung():
    sql = db._postgres_migration_sql(
        "CREATE TABLE x (id INTEGER PRIMARY KEY, erstellt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
    )
    assert "id BIGSERIAL PRIMARY KEY" in sql
    assert "DEFAULT (CURRENT_TIMESTAMP::text)" in sql


def test_postgres_url_erkennung_ist_explizit():
    assert not "mysql://example".startswith(("postgresql://", "postgres://"))
