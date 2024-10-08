
# This module contains the functions that are used to configure the input and output of the workflow for the current app.

import supervisely as sly
from typing import Literal

def workflow_input(api):
    raise NotImplementedError

def workflow_output(api: sly.Api, id: int, type: Literal["project", "dataset"]):
    if type == "project":
        api.app.workflow.add_output_project(id)
        sly.logger.debug(f"Workflow: Output project - {id}")
    elif type == "dataset":
        api.app.workflow.add_output_dataset(id)
        sly.logger.debug(f"Workflow: Output dataset - {id}")