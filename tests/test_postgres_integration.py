import os
import secrets
import sys

import pytest


POSTGRES_TEST_URL = os.environ.get("POSTGRES_TEST_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_TEST_URL, reason="POSTGRES_TEST_URL ist nicht gesetzt")


def test_postgres_schema_und_anwendungszugriffe():
    # db liest die URL beim Import; der CI-/Smoke-Test setzt beide Werte auf dieselbe isolierte Datenbank.
    assert os.environ.get("DATABASE_URL") == POSTGRES_TEST_URL
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
    import db
    from core import app, exe, one

    suffix = secrets.token_hex(6)
    with app.app_context():
        assert db.schema_version() == len(db.MIGRATIONEN)
        uid = exe("INSERT INTO benutzer (benutzername, passwort_hash, rolle) VALUES (?, ?, ?)",
                  (f"Pg-{suffix}", "test", "admin"))
        assert isinstance(uid, int)
        assert one("SELECT id FROM benutzer WHERE benutzername = ? COLLATE NOCASE", (f"pg-{suffix}",))["id"] == uid
        iid = exe("INSERT INTO immobilie (name, ordner) VALUES (?, ?)", (f"PostgreSQL {suffix}", suffix))
        assert one("SELECT name FROM immobilie WHERE id = ?", (iid,))["name"] == f"PostgreSQL {suffix}"
        exe("DELETE FROM immobilie WHERE id = ?", (iid,))
        exe("DELETE FROM benutzer WHERE id = ?", (uid,))

    client = app.test_client()
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200
