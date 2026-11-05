"""Injeta regressões selecionadas em uma cópia temporária e exige testes falhando.

Execute: .venv/bin/python scripts/audit_error_mutations.py --report /tmp/error-mutations.json
Não altera fontes locais, não conecta ao PostgreSQL e não substitui mutação exaustiva.
"""

import argparse
import ast
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Mutation:
    name: str
    path: str
    before: str
    after: str
    tests: str


PACKAGE = "src/api_performance_monitor/"
MUTATIONS = (
    Mutation("accept-boolean-latency", "domain/validation.py",
             'if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):\n        raise error',
             'if not isinstance(value, (Real, Decimal)):\n        raise error', "tests/domain"),
    Mutation("accept-negative-latency", "domain/validation.py",
             "if value < 0:", "if False:", "tests/domain"),
    Mutation("accept-nonfinite-latency", "domain/validation.py",
             'if not isfinite(number):\n        raise error',
             'if False:\n        raise error', "tests/domain"),
    Mutation("accept-percentile-101", "domain/validation.py",
             "if not 0 <= value <= 100:", "if not 0 <= value <= 101:", "tests/domain"),
    Mutation("count-threshold-as-above", "domain/latency.py",
             "sum(value > limit for value", "sum(value >= limit for value", "tests/roots/test_statistics_routes.py"),
    Mutation("allow-one-sample-variance", "domain/statistics.py",
             "if sample and len(values) < 2:", "if False:", "tests/domain"),
    Mutation("ignore-sample-query", "roots/statistics_root.py",
             "variance = dataset.variance(sample=sample)", "variance = dataset.variance(sample=False)",
             "tests/roots/test_statistics_routes.py"),
    Mutation("ignore-percentile-query", "roots/statistics_root.py",
             "percentile = dataset.percentile(percent)", "percentile = dataset.percentile(95)",
             "tests/roots/test_statistics_routes.py"),
    Mutation("ignore-threshold-query", "roots/statistics_root.py",
             "count_above = dataset.count_above(threshold_ms)", "count_above = dataset.count_above(120)",
             "tests/roots/test_statistics_routes.py"),
    Mutation("ignore-measurement-filter", "services/latency_dataset_service.py",
             "if value is None or measurement.latency_ms == value", "if True", "tests/roots/test_resource_routes.py"),
    Mutation("delete-before-reporting-conflict", "services/latency_dataset_service.py",
             '            raise DatasetWouldBecomeEmptyError("A última medição não pode ser removida.")',
             '            self.db.delete(measurement)\n            self.db.commit()\n'
             '            raise DatasetWouldBecomeEmptyError("A última medição não pode ser removida.")',
             "tests/roots/test_input_errors.py"),
    Mutation("ignore-measurement-id", "services/latency_dataset_service.py",
             "if measurement.id == measurement_id:", "if True:", "tests/roots/test_input_errors.py"),
    Mutation("coerce-http-booleans", "schemas/latency_dataset_schema.py",
             "if isinstance(value, bool):", "if False:", "tests/roots/test_input_errors.py"),
    Mutation("wrong-not-found-status", "errors/http_error_handlers.py",
             "status_code=status.HTTP_404_NOT_FOUND,", "status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,", "tests/errors"),
    Mutation("wrong-conflict-status", "errors/http_error_handlers.py",
             "status_code = status.HTTP_409_CONFLICT", "status_code = status.HTTP_422_UNPROCESSABLE_CONTENT", "tests/errors"),
    Mutation("render-wrong-chart", "roots/visualization_root.py",
             "return _png_response(dataset, create_latency_timeline)",
             "return _png_response(dataset, create_latency_frequency_chart)", "tests/roots/test_visualization_routes.py"),
    Mutation("wrong-png-media-type", "roots/visualization_root.py",
             'media_type="image/png"', 'media_type="application/json"', "tests/roots/test_visualization_routes.py"),
    Mutation("leak-failed-export-buffer", "visualization/export.py",
             "        buffer.close()\n", "        pass\n", "tests/visualization/test_export.py"),
    Mutation("skip-failed-chart-cleanup", "roots/visualization_root.py",
             "figure.clear()", "pass", "tests/roots/test_unexpected_errors.py"),
    Mutation("accept-zero-resource-id", "schemas/path_parameters.py",
             "Path(ge=1,", "Path(ge=0,", "tests/roots/test_input_errors.py"),
)


def run_tests(workspace, environment, selector):
    report = workspace / "junit.xml"
    report.unlink(missing_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
         f"--junitxml={report}", *selector.split()],
        cwd=workspace, env=environment, capture_output=True, text=True, timeout=60,
    )
    if not report.exists():
        return {"status": "invalid", "exit_code": result.returncode, "output": result.stdout + result.stderr}
    suites = ET.parse(report).getroot().findall("testsuite")
    failures = sum(int(suite.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.get("errors", 0)) for suite in suites)
    tests = sum(int(suite.get("tests", 0)) for suite in suites)
    skipped = sum(int(suite.get("skipped", 0)) for suite in suites)
    status = "invalid"
    if result.returncode == 0 and tests > 0 and not skipped and not errors and not failures:
        status = "passed"
    elif result.returncode == 1 and failures > 0 and not errors:
        status = "detected"
    return {"status": status, "exit_code": result.returncode, "tests": tests,
            "failures": failures, "errors": errors, "skipped": skipped,
            "failed_cases": [case.get("name") for case in ET.parse(report).iter("testcase")
                             if case.find("failure") is not None],
            "output": result.stdout + result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    results = []
    with tempfile.TemporaryDirectory(prefix="api-error-mutations-") as temporary:
        workspace = Path(temporary)
        for directory in ("src", "tests"):
            shutil.copytree(root / directory, workspace / directory,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        for filename in ("main.py", "pyproject.toml"):
            shutil.copy2(root / filename, workspace / filename)
        environment = {**os.environ, "PYTHONPATH": os.pathsep.join((str(workspace / "src"), str(workspace))),
                       "PYTHONDONTWRITEBYTECODE": "1"}
        # A instalação editable não pode direcionar os testes ao código original.
        probe = subprocess.run(
            [sys.executable, "-c", "import api_performance_monitor as p; print(p.__file__)"],
            cwd=workspace, env=environment, capture_output=True, text=True, check=True,
        )
        if not Path(probe.stdout.strip()).is_relative_to(workspace):
            raise RuntimeError("A importação escapou da cópia temporária.")
        # Verifica todos os alvos antes de gastar tempo executando a auditoria.
        for mutation in MUTATIONS:
            original = (workspace / PACKAGE / mutation.path).read_text()
            if original.count(mutation.before) != 1:
                raise RuntimeError(f"Mutação desatualizada ou ambígua: {mutation.name}")
            ast.parse(original.replace(mutation.before, mutation.after))
        baseline = run_tests(workspace, environment, "tests")
        if baseline["status"] != "passed":
            print(baseline["output"])
            raise RuntimeError("A suíte original precisa passar sem skips antes das mutações.")
        print(f"Controle: {baseline['tests']} testes passaram na cópia isolada.", flush=True)
        for mutation in MUTATIONS:
            path = workspace / PACKAGE / mutation.path
            original = path.read_text()
            if original.count(mutation.before) != 1:
                raise RuntimeError(f"Mutação desatualizada ou ambígua: {mutation.name}")
            mutated = original.replace(mutation.before, mutation.after)
            ast.parse(mutated)
            try:
                path.write_text(mutated)
                outcome = run_tests(workspace, environment, mutation.tests)
            finally:
                path.write_text(original)
            outcome.update(name=mutation.name, path=mutation.path, selector=mutation.tests)
            results.append(outcome)
            print(f"{mutation.name}: {outcome['status']} ({outcome.get('failures', 0)} falhas)", flush=True)
        summary = {"baseline": baseline, "mutations": results,
                   "detected": sum(item["status"] == "detected" for item in results),
                   "total": len(results)}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
        print(f"Relatório: {args.report}", flush=True)
        return 0 if summary["detected"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
