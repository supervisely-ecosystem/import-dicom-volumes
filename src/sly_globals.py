import os
from distutils.util import strtobool

import supervisely as sly
from dotenv import load_dotenv
from supervisely.app.v1.app_service import AppService
from supervisely.io.fs import mkdir

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()
my_app: AppService = AppService()

TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
TASK_ID = int(os.environ["TASK_ID"])

SELECTED_SLY_CONTEXT = os.environ.get("context.slySelectedContext")

if SELECTED_SLY_CONTEXT == "agent_folder" or SELECTED_SLY_CONTEXT == "agent_file":
    IS_ON_AGENT = True
else:
    IS_ON_AGENT = False

# if existing project (or dataset) is selected
SLY_PROJECT_ID = os.environ.get("modal.state.slyProjectId") or None
SLY_DATASET_ID = os.environ.get("modal.state.slyDatasetId") or None
PROJECT_ID = os.environ.get("modal.state.projectId") or SLY_PROJECT_ID
DATASET_ID = os.environ.get("modal.state.datasetId") or SLY_DATASET_ID

if PROJECT_ID is not None:
    PROJECT_ID = int(PROJECT_ID)
if DATASET_ID is not None:
    DATASET_ID = int(DATASET_ID)

INPUT_DIR: str = os.environ.get("modal.state.slyFolder", None)
INPUT_FILE: str = os.environ.get("modal.state.slyFile", None)
INPUT_FILES: str = os.environ.get("modal.state.files", None)

sly.logger.info(f"INPUT_FILES: {INPUT_FILES}, INPUT_DIR: {INPUT_DIR}, INPUT_FILE: {INPUT_FILE}")

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
elif INPUT_FILE:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILES)


OUTPUT_PROJECT_NAME = os.environ.get("modal.state.dstProjectName", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.removeSource")))

DEFAULT_DATASET_NAME = "ds0"
ANONYMIZE_VOLUMES = bool(strtobool(os.getenv("modal.state.anonymizeVolumes")))

STORAGE_DIR: str = my_app.data_dir
mkdir(STORAGE_DIR, True)
