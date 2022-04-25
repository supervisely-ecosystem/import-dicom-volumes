import os

import magic

# import mimetypes
import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g
from src.volume_reader import process_file
from supervisely.volume.parsers import dicom

# @TODO: new project / append to existing project
# @TODO: test nrrd and nifty
# @TODO: https://pydicom.github.io/pydicom/dev/auto_examples/image_processing/reslice.html
# @TODO: https://simpleitk.readthedocs.io/en/master/link_DicomSeriesReader_docs.html
# @TODO: reoriented = sitk.DICOMOrient(img, 'RAS')

sly.logger.info("Application has been started")
print("hey there")


path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
project_name = "test"
dataset_name = "ds-01"

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)

total_counter = 0
for root, dirs, files in os.walk(path):
    dir_has_dcm_files = False

    for entry_name in files:
        full_entry_name = os.path.join(root, entry_name)
        entry_mime = magic.from_file(full_entry_name, mime=True)

        if entry_mime == "application/dicom":
            dir_has_dcm_files = True

        # entry_name_low = entry_name.lower()
        # if entry_name_low.endswith("nrrd") or entry_name_low.endswith("nrrd.gz"):
        #     parser_type = "nrrd"
        # elif entry_name_low.endswith("nii") or entry_name_low.endswith("nii.gz"):
        #     parser_type = "nifti"
        # elif entry_name_low.endswith("dcm"):
        #     dir_has_dcm_files = True
        # else:
        #     pass
        # if parser_type is not None:
        #     total_counter += process_file(
        #         g.api, project, dataset, full_entry_name, parser_type
        #     )
        # else:
        #     raise NotImplementedError("file without extension")

    if dir_has_dcm_files:
        total_counter += process_file(g.api, project, dataset, root, "dicom")

f.shutdown_app()
