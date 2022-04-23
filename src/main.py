import supervisely as sly
from supervisely import logger

sly.app.fastapi

import src.sly_functions as f
import src.sly_globals as g


logger.info("Application has been started")

################
# your code here
################

print(123)

f.shutdown_app()
