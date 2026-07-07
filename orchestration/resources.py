"""Shared paths and the dbt resource for the orchestration package.

Centralises three things every asset module needs:
  * REPO_ROOT / data paths,
  * making scripts/ importable (they are plain scripts, not an installed pkg),
  * the DbtProject + DbtCliResource wiring.
"""

from __future__ import annotations

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

# The refresh scripts (download_raw.py, load_to_duckdb.py, build_decision_db.py)
# are plain scripts, not an installed package — put scripts/ on the path so the
# assets can import and call their functions directly instead of shelling out.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# When `dagster dev` spawns the code server, the venv's Scripts/bin dir is not
# on PATH, so the `dbt` executable and dbt's own subprocesses can't be found.
# Prepend it (the dir holding the running python) so dbt resolves in every child.
VENV_BIN = Path(sys.executable).parent
os.environ["PATH"] = str(VENV_BIN) + os.pathsep + os.environ.get("PATH", "")

# A stale partial-parse cache from the pre-rename project path
# (project-2-uk-analytics) still bites full builds; disable partial parse so
# dbt always reparses cleanly here. See MoveIn "Local dbt facts".
os.environ.setdefault("DBT_PARTIAL_PARSE", "false")

# The dbt profile `uk_property_analytics` lives in ~/.dbt/profiles.yml (dbt's
# default location). DbtProject.prepare_if_dev() and DbtCliResource both default
# profiles_dir to the project dir (which has no profiles.yml), so export
# DBT_PROFILES_DIR to steer every dbt invocation. Override in CI if needed.
PROFILES_DIR = os.environ.setdefault("DBT_PROFILES_DIR", str(Path.home() / ".dbt"))
DBT_EXECUTABLE = shutil.which("dbt") or str(VENV_BIN / "dbt.exe")

dbt_project = DbtProject(project_dir=REPO_ROOT, profiles_dir=PROFILES_DIR)
dbt_project.prepare_if_dev()

dbt_resource = DbtCliResource(
    project_dir=dbt_project,
    profiles_dir=PROFILES_DIR,
    dbt_executable=DBT_EXECUTABLE,
)
