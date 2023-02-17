import supervisely as sly

import sly_functions as f
import sly_globals as g


@g.my_app.callback("import-dicom-volumes")
@sly.timeit
def import_dicom_volumes(
    api: sly.Api, task_id: int, context: dict, state: dict, app_logger
) -> None:

    project_dir = f.download_data_from_team_files(api=api, task_id=task_id, save_path=g.STORAGE_DIR)
    project_name = (
        f.get_project_name_from_input_path(project_dir)
        if len(g.OUTPUT_PROJECT_NAME) == 0
        else g.OUTPUT_PROJECT_NAME
    )

    project = g.api.project.create(
        workspace_id=g.WORKSPACE_ID,
        name=project_name,
        type=sly.ProjectType.VOLUMES,
        change_name_if_conflict=True,
    )
    dataset = g.api.dataset.create(
        project_id=project.id, name=g.DEFAULT_DATASET_NAME, change_name_if_conflict=True
    )

    used_volumes_names = []

    # DICOM
    series_infos = sly.volume.inspect_dicom_series(root_dir=project_dir)
    for serie_id, files in series_infos.items():
        item_path = files[0]
        if sly.volume.get_extension(path=item_path) is None:
            sly.logger.warn(f"Can not recognize file extension {item_path}, serie will be skipped")
            continue
        name = f"{serie_id}.nrrd"
        name = f.generate_free_name(
            used_names=used_volumes_names, possible_name=name, with_ext=True
        )
        used_volumes_names.append(name)
        g.api.volume.upload_dicom_serie_paths(
            dataset_id=dataset.id,
            name=name,
            paths=files,
            log_progress=True,
            anonymize=g.ANONYMIZE_VOLUMES,
        )

    # NRRD
    nrrd_paths = sly.volume.inspect_nrrd_series(root_dir=project_dir)
    for nrrd_path in nrrd_paths:
        name = sly.fs.get_file_name_with_ext(path=nrrd_path)
        name = f.generate_free_name(
            used_names=used_volumes_names, possible_name=name, with_ext=True
        )
        used_volumes_names.append(name)
        g.api.volume.upload_nrrd_serie_path(
            dataset_id=dataset.id, name=name, path=nrrd_path, log_progress=True
        )

    if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
        if g.INPUT_DIR is not None:
            path_to_remove = g.INPUT_DIR
        else:
            path_to_remove = g.INPUT_FILE
        api.file.remove(team_id=g.TEAM_ID, path=path_to_remove)
        source_dir_name = path_to_remove.lstrip("/").rstrip("/")
        sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")

    g.my_app.stop()


def main():
    sly.logger.info(
        "Script arguments", extra={"TEAM_ID": g.TEAM_ID, "WORKSPACE_ID": g.WORKSPACE_ID}
    )
    g.my_app.run(initial_events=[{"command": "import-dicom-volumes"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
