import os
import subprocess
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "app")


def test_web_import_migriert_nicht(tmp_path):
    data = tmp_path / "data"
    env = {**os.environ, "NK_DATA": str(data), "NK_DOKUMENTE": str(tmp_path / "docs"),
           "PYTHONPATH": APP, "SECRET_KEY": "test-secret"}
    subprocess.run([sys.executable, "-c", "import main"], cwd=APP, env=env, check=True)
    assert not (data / "nebenkosten.sqlite").exists()


def test_migrationskommando_legt_aktuelles_schema_an(tmp_path):
    data = tmp_path / "data"
    env = {**os.environ, "NK_DATA": str(data), "PYTHONPATH": APP}
    result = subprocess.run([sys.executable, "manage.py", "migrate"], cwd=APP, env=env, check=True,
                            capture_output=True, text=True)
    assert "Version 22" in result.stdout
    assert (data / "nebenkosten.sqlite").exists()
