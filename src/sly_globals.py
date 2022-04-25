import os
from fastapi import FastAPI
from dotenv import load_dotenv
import supervisely as sly

app_root_directory = os.getcwd()
sly.logger.info(f"App root directory: {app_root_directory}")

# order matters
load_dotenv(os.path.join(app_root_directory, "debug_secret.env"))
load_dotenv(os.path.join(app_root_directory, "debug.env"))

app = FastAPI()
sly_app = sly.app.fastapi.create()
app.mount("/sly", sly_app)

api = sly.Api.from_env()

# task_id = int(os.environ["TASK_ID"])
team_id = int(os.environ["context.teamId"])
workspace_id = int(os.environ["context.workspaceId"])
