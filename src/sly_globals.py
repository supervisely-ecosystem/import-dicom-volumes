import os
import sys
from distutils.util import strtobool
from pathlib import Path

import supervisely as sly
from dotenv import load_dotenv
from supervisely.app.v1.app_service import AppService
from supervisely.io.fs import mkdir

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()
my_app: AppService = AppService()

TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
TASK_ID = int(os.environ["TASK_ID"])

INPUT_DIR: str = os.environ.get("modal.state.slyFolder", None)
INPUT_FILE: str = os.environ.get("modal.state.slyFile", None)

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)

OUTPUT_PROJECT_NAME = os.environ.get("modal.state.project_name", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))

DEFAULT_DATASET_NAME = "ds0"
ANONYMIZE_VOLUMES = bool(strtobool(os.getenv("modal.state.anonymizeVolumes")))

STORAGE_DIR: str = my_app.data_dir
mkdir(STORAGE_DIR, True)
