"""Shared paths and the dbt resource for the orchestration package.

Centralises three things every asset module needs:
  * REPO_ROOT / data paths,
  * making scripts/ importable (they are plain scripts, not an installed pkg),
  * the DbtProject + DbtCliResource wiring.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from dagster_dbt import DbtCliResource, DbtProject

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
DATA_DIR = REPO_ROOT / "data"
RAW_GLOB = (DATA_DIR / "raw" / "pp-*.parquet").as_posix()
WAREHOUSE_DB = DATA_DIR / "warehouse.duckdb"

# The refresh scripts (download_raw.py, load_*.py, build_decision_db.py) are
# plain scripts, not an installed package. Import them by explicit file path:
# a sys.path side-effect at definitions-import time does NOT reliably survive
# into Dagster's spawned step workers on Windows, so path-based import is the
# only execution-safe way for assets to call the script functions directly.


def load_script(name: str):
    """Import scripts/<name>.py as a module, bypassing sys.path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # Register so any pickling / repeated import inside a step reuses it.
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module

# When `dagster dev` spawns the code server, the venv's Scripts/bin dir is not
# on PATH, so the `dbt` executable and dbt's own subprocesses can't be found.
# Prepend it (the dir holding the running python) so dbt resolves in every child.
VENV_BIN = Path(sys.executable).parent
os.environ["PATH"] = str(VENV_BIN) + os.pathsep + os.environ.get("PATH", "")

# A stale partial-parse cache from the pre-rename project path
# (project-2-uk-analytics) still bites full builds; disable partial parse so
# dbt always reparses cleanly here. See the project runbook's local dbt notes.
os.environ.setdefault("DBT_PARTIAL_PARSE", "false")

# Windows step workers get cp1252 stdout, so a script print containing a
# non-cp1252 character (e.g. '→') raises UnicodeEncodeError and fails the step
# AFTER the actual work succeeded. Force UTF-8 for this process and children.
os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# The dbt profile `uk_property_analytics` lives in ~/.dbt/profiles.yml (dbt's
# default location). DbtProject.prepare_if_dev() and DbtCliResource both default
# profiles_dir to the project dir (which has no profiles.yml), so export
# DBT_PROFILES_DIR to steer every dbt invocation. Override in CI if needed.
PROFILES_DIR = os.environ.setdefault("DBT_PROFILES_DIR", str(Path.home() / ".dbt"))
DBT_EXECUTABLE = shutil.which("dbt") or str(VENV_BIN / "dbt.exe")

# The orchestrated pipeline IS the real refresh, so parse AND build with the
# real-source vars. This matters at parse time, not just build time: the staging
# models switch on these vars between the committed fixture seeds (CI default)
# and the raw_* warehouse schemas, so a fixture-vars manifest would wire staging
# to the seeds and leave the ingestion assets disconnected from the dbt graph.
REAL_SOURCE_VARS = {
    "geo_source": "onspd",
    "epc_source": "bulk",
    "crime_source": "bulk",
    "constraints_source": "computed",
    "amenities_source": "computed",
}
REAL_SOURCE_VARS_JSON = json.dumps(REAL_SOURCE_VARS)

dbt_project = DbtProject(
    project_dir=REPO_ROOT,
    profiles_dir=PROFILES_DIR,
    prepare_project_cli_args=["parse", "--quiet", "--vars", REAL_SOURCE_VARS_JSON],
)
dbt_project.prepare_if_dev()

dbt_resource = DbtCliResource(
    project_dir=dbt_project,
    profiles_dir=PROFILES_DIR,
    dbt_executable=DBT_EXECUTABLE,
)
