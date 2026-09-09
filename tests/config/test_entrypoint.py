"""The production entrypoint must reach a working HTTP server."""

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from sqlalchemy.engine import make_url

from tests.test_config import Config


def test_entrypoint_serves_health_after_migration_and_seed(_db, tmp_path):
    database = make_url(Config.URI)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    env = {
        **os.environ,
        "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}",
        "FLASK_APP": "run.py",
        "FLASK_DEBUG": "0",
        "DATABASE_HOST": database.host or "localhost",
        "DATABASE_PORT": str(database.port or 5432),
        "POSTGRES_USER": database.username or "",
        "POSTGRES_PASSWORD": database.password or "",
        "POSTGRES_DB": database.database or "",
        "SECRET_KEY": Config.SECRET_KEY,
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "BACKUP_DIR": str(tmp_path / "backups"),
        "GIT_SHA": "entrypoint-test",
        "GUNICORN_CMD_ARGS": (
            f"--bind 127.0.0.1:{port} --workers 1 --worker-tmp-dir {tmp_path}"
        ),
    }
    log_path = tmp_path / "startup.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            ["bash", "entrypoint.sh"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    with urlopen(
                        f"http://127.0.0.1:{port}/health", timeout=1
                    ) as response:
                        assert json.load(response) == {
                            "status": "healthy",
                            "version": "entrypoint-test",
                        }
                        return
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            pytest.fail(f"Entrypoint did not become healthy:\n{log_path.read_text()}")
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
