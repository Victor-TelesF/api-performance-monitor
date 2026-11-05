"""Regressões da leitura da saída do Docker, sem depender de imagens em cache."""

import subprocess

import pytest

from scripts.check_docker_deploy import docker


@pytest.fixture()
def fake_docker(tmp_path, monkeypatch):
    executable = tmp_path / "docker"
    monkeypatch.setenv("PATH", str(tmp_path))

    def install(body: str) -> None:
        executable.write_text("#!/bin/sh\n" + body)
        executable.chmod(0o755)

    return install


@pytest.mark.parametrize("downloading", [False, True])
def test_container_id_excludes_download_messages(fake_docker, capfd, downloading):
    container_id = "a" * 64
    diagnostics = (
        "Unable to find image 'postgres:17' locally\n17: Pulling from library/postgres\n"
        if downloading else ""
    )
    fake_docker(
        f"printf '%s' \"{diagnostics}\" >&2\n"
        f"printf '%s\\n' '{container_id}'\n"
    )

    assert docker("run", "--detach", "postgres:17") == container_id
    assert capfd.readouterr().err == diagnostics


def test_container_logs_include_stderr(fake_docker):
    fake_docker(
        "printf 'Starting migration\\n'\n"
        "printf 'connection refused\\n' >&2\n"
    )

    logs = docker("logs", "container-id", merge_output=True)

    assert "Starting migration" in logs
    assert "connection refused" in logs


def test_docker_failure_preserves_diagnostics(fake_docker, capfd):
    fake_docker("printf 'Docker daemon unavailable\\n' >&2\nexit 125\n")

    with pytest.raises(subprocess.CalledProcessError) as error:
        docker("run", "--detach", "postgres:17")

    assert error.value.returncode == 125
    assert "Docker daemon unavailable" in capfd.readouterr().err
