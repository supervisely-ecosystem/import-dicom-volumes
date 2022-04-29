import os

import supervisely as sly
import src.sly_globals as g
import SimpleITK as sitk

sly.logger.info("Application has been started")
print("hey there")

project_name = "nrrd"
dataset_name = "ds"
# @TODO: add version to volume meta!!
# @TODO: add anonymize flag in modal window

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_info_by_name(project.id, dataset_name)
if dataset is not None:
    g.api.dataset.remove(dataset.id)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)


# test nrrd example
path = "/Users/max/work/ras-dcm-test-dimentions-private"
nrrd_paths = sly.volume.inspect_nrrd_series(path)
for nrrd_path in nrrd_paths:
    name = sly.fs.get_file_name_with_ext(nrrd_path)
    g.api.volume.upload_nrrd_serie_path(dataset.id, name, nrrd_path, True)
sly.app.fastapi.shutdown()
exit(0)

# test dicom examples
# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# path = "/Users/max/work/dicom-private-test/1.2.840.113704.1.111.6000.1606737510.1"
# path = "/Users/max/work/dicom-for-ecosystem/lera"
series_infos = sly.volume.inspect_dicom_series(path)
for serie_id, files in series_infos.items():
    item_path = files[0]
    if sly.volume.get_extension(item_path) is None:
        sly.logger.warn(
            f"Can not recognize file extension {item_path}, serie will be skipped"
        )
        continue
    name = f"{sly.fs.get_file_name(item_path)}.nrrd"
    res = g.api.volume.upload_dicom_serie_paths(dataset.id, name, files, True)

sly.app.fastapi.shutdown()
exit(0)
