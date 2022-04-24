import supervisely as sly
from supervisely import logger

import src.sly_functions as f
import src.sly_globals as g

logger.info("Application has been started")

path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"


def main():
    print("hey there")
    f.shutdown_app()


if __name__ == "__main__":
    main()
