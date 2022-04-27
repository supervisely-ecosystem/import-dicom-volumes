import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g


sly.logger.info("Application has been started")
print("hey there")


project_name = "test"
dataset_name = "ds-01"

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_info_by_name(project.id, dataset_name)
if dataset is not None:
    g.api.dataset.remove(dataset.id)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)

# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# nifti examples
# path = "/Users/max/work/medsi-mrt-duplicate/nifti"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/den-mrt/45130000"

# @TODO: volume.upload_np - add progresses

series_infos = sly.volume.inspect_series(path)

for (files, meta) in series_infos:
    item_path = files[0]
    if sly.volume.get_extension(item_path) is None:
        sly.logger.warn(
            f"Can not recognize file extension {item_path}, serie will be skipped"
        )
        continue
    name = f"{sly.fs.get_file_name(item_path)}.nrrd"
    res = g.api.volume.upload_dicom_serie_paths(dataset.id, name, files, meta)


f.shutdown_app()
