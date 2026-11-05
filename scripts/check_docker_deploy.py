"""Valida a imagem de produção com PostgreSQL descartável, sem ler o .env.

Execute depois do build: python scripts/check_docker_deploy.py --image TAG
Não publica portas nem usa volumes persistentes ou o banco de produção.
"""

import argparse
import json
import subprocess
import sys
import time


def docker(*args: str, merge_output: bool = False) -> str:
    result = subprocess.run(
        ["docker", *args], text=True, capture_output=True, timeout=120
    )
    # Downloads e avisos vão para stderr; stdout pode conter apenas um ID.
    if result.stderr and not merge_output:
        print(result.stderr, file=sys.stderr, end="")
    result.check_returncode()
    output = result.stdout + result.stderr if merge_output else result.stdout
    return output.strip()


def wait_for(container: str, command: list[str]) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", container, *command],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return
        if docker("inspect", "--format", "{{.State.Running}}", container) != "true":
            break
        time.sleep(0.5)
    raise RuntimeError(
        f"Container não ficou pronto:\n{docker('logs', container, merge_output=True)}"
    )


def check(image: str) -> None:
    containers: list[str] = []

    def start(*args: str) -> str:
        container = docker("run", "--detach", *args)
        containers.append(container)
        return container

    def python_in(container: str, code: str) -> str:
        return docker("exec", container, "/app/.venv/bin/python", "-c", code)

    try:
        database = start(
            "--network", "none", "--tmpfs", "/var/lib/postgresql/data",
            "--env", "POSTGRES_USER=ci_user", "--env", "POSTGRES_PASSWORD=ci_password",
            "--env", "POSTGRES_DB=ci_db", "postgres:17",
        )
        wait_for(database, ["pg_isready", "-h", "127.0.0.1", "-U", "ci_user", "-d", "ci_db"])
        environment = [
            "--network", f"container:{database}", "--env", "PORT=12345",
            "--env", "POSTGRES_HOST=127.0.0.1", "--env", "POSTGRES_PORT=5432",
            "--env", "POSTGRES_USER=ci_user", "--env", "POSTGRES_PASSWORD=ci_password",
            "--env", "POSTGRES_DB=ci_db",
        ]
        api = start(*environment, image)
        wait_for(api, [
            "/app/.venv/bin/python", "-c",
            'import urllib.request; assert urllib.request.urlopen('
            '"http://127.0.0.1:12345/openapi.json", timeout=2).status == 200',
        ])
        tables = docker(
            "exec", database, "psql", "-U", "ci_user", "-d", "ci_db", "-Atc",
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
        )
        assert set(tables.splitlines()) == {
            "alembic_version", "latency_datasets", "latency_measurements",
        }, tables
        revision = python_in(api, """
from sqlalchemy import text
from api_performance_monitor.database import db_engine
from alembic.config import Config
from alembic.script import ScriptDirectory
with db_engine.connect() as connection:
    actual = connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
assert actual == ScriptDirectory.from_config(Config('alembic.ini')).get_current_head()
print(actual)
"""
        )
        dataset = json.loads(python_in(api, """
import json
import urllib.request
request = urllib.request.Request(
    'http://127.0.0.1:12345/datasets',
    data=json.dumps({'latency_ms': [100, 120, 150]}).encode(),
    headers={'Content-Type': 'application/json'},
)
with urllib.request.urlopen(request, timeout=5) as response:
    assert response.status == 201
    print(response.read().decode())
"""
        ))
        assert dataset["latency_ms"] == [100, 120, 150]
        print(f"Alembic na revisão {revision}; criação de dataset: HTTP 201.", flush=True)

        # Reiniciar o mesmo container executa novamente o CMD no banco já migrado.
        docker("restart", "--time", "5", api)
        wait_for(api, [
            "/app/.venv/bin/python", "-c",
            "import json, urllib.request; "
            f"response=urllib.request.urlopen('http://127.0.0.1:12345/datasets/{dataset['id']}', timeout=2); "
            "assert json.load(response)['latency_ms'] == [100, 120, 150]",
        ])
        print("Reinicialização preservou o dataset e as migrações.", flush=True)

        failed_api = start(
            "--network", "none", "--env", "POSTGRES_HOST=127.0.0.1",
            "--env", "POSTGRES_PORT=1", "--env", "POSTGRES_USER=ci_user",
            "--env", "POSTGRES_PASSWORD=ci_password", "--env", "POSTGRES_DB=ci_db", image,
        )
        assert docker("wait", failed_api) != "0"
        logs = docker("logs", failed_api, merge_output=True)
        assert "connection refused" in logs.lower(), logs
        assert "Uvicorn running" not in logs, logs
        print("Falha de migração impediu a inicialização do servidor.", flush=True)
    finally:
        for container in reversed(containers):
            subprocess.run(
                ["docker", "rm", "--force", "--volumes", container],
                capture_output=True, timeout=30,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="api-performance-monitor:ci")
    check(parser.parse_args().image)
