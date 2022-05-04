import os

import supervisely as sly

import sly_functions as f
import src.sly_globals as g


@g.my_app.callback("import-dicom-volumes")
@sly.timeit
def import_images_groups(
    api: sly.Api, task_id: int, context: dict, state: dict, app_logger
) -> None:

    project_dir = f.download_data_from_team_files(
        api=api, task_id=task_id, save_path=g.STORAGE_DIR
    )
    project_name = os.path.basename(project_dir)

    project = g.api.project.create(
        g.WORKSPACE_ID,
        project_name,
        type=sly.ProjectType.VOLUMES,
        change_name_if_conflict=True,
    )
    dataset = g.api.dataset.create(
        project_id=project.id, name=g.DEFAULT_DATASET_NAME, change_name_if_conflict=True
    )

    # DICOM
    series_infos = sly.volume.inspect_dicom_series(project_dir)
    for serie_id, files in series_infos.items():
        item_path = files[0]
        if sly.volume.get_extension(item_path) is None:
            sly.logger.warn(
                f"Can not recognize file extension {item_path}, serie will be skipped"
            )
            continue
        name = f"{sly.fs.get_file_name(item_path)}.nrrd"
        g.api.volume.upload_dicom_serie_paths(dataset.id, name, files, True)

    # NRRD
    nrrd_paths = sly.volume.inspect_nrrd_series(project_dir)
    for nrrd_path in nrrd_paths:
        name = sly.fs.get_file_name_with_ext(nrrd_path)
        g.api.volume.upload_nrrd_serie_path(dataset.id, name, nrrd_path, True)

    g.my_app.stop()


def main():
    sly.logger.info(
        "Script arguments", extra={"TEAM_ID": g.TEAM_ID, "WORKSPACE_ID": g.WORKSPACE_ID}
    )
    g.my_app.run(initial_events=[{"command": "import-dicom-volumes"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)

# @TODO: add version to volume meta!!
# @TODO: add anonymize flag in modal window
