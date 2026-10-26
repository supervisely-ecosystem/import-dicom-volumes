import os

import supervisely as sly

import sly_functions as f
import sly_globals as g
import workflow as w


@g.my_app.callback("import-dicom-volumes")
@sly.timeit
def import_dicom_volumes(
    api: sly.Api, task_id: int, context: dict, state: dict, app_logger
) -> None:
    # The exact Team Files path the user selected (or the app-owned drag-and-drop folder
    # /import/import-dicom-volumes/<formId>/). download_data_from_team_files() may re-point
    # g.INPUT_DIR to the parent folder of a selected file; that parent must never be removed.
    selected_path = g.INPUT_DIR or g.INPUT_FILES or g.INPUT_FILE
    save_path = f.download_data_from_team_files(api=api, task_id=task_id, save_path=g.STORAGE_DIR)
    if save_path:
        # every downloaded file, listed before upload: anything not imported keeps the source
        downloaded_files = sly.fs.list_files_recursively(save_path)
        imported_files = []
        project_dir = f.get_project_dir(path=save_path)

        # DICOM
        series_infos = sly.volume.inspect_dicom_series(root_dir=project_dir)
        # NRRD
        nrrd_paths = sly.volume.inspect_nrrd_series(root_dir=project_dir)
        # found series that were skipped: if any, the source is kept
        skipped_series = []

        if len(series_infos) == 0 and len(nrrd_paths) == 0:
            msg = "No DICOM volumes were found. Please, check your input directory."
            description = (
                f"Supported formats: {g.ALLOWED_VOLUME_EXTENSIONS} (in archive or directory)."
            )
            sly.logger.warn(f"{msg} {description}")
            api.task.set_output_error(task_id, msg, description)
            _keep_source(selected_path, msg)
            g.my_app.stop()
            return

        else:
            if g.PROJECT_ID is None:
                project_name = (
                    f.get_project_name_from_input_path(project_dir) or "DICOM Volumes project"
                    if len(g.OUTPUT_PROJECT_NAME.strip()) == 0
                    else g.OUTPUT_PROJECT_NAME
                )

                sly.logger.debug(
                    f"Result project name: {project_name}, Input project name: {g.OUTPUT_PROJECT_NAME}"
                )

                project = g.api.project.create(
                    workspace_id=g.WORKSPACE_ID,
                    name=project_name,
                    type=sly.ProjectType.VOLUMES,
                    change_name_if_conflict=True,
                )
            else:
                project = api.project.get_info_by_id(g.PROJECT_ID)

            if g.DATASET_ID is None:
                dataset = g.api.dataset.create(
                    project_id=project.id, name=g.DEFAULT_DATASET_NAME, change_name_if_conflict=True
                )
                used_volumes_names = []
            else:
                dataset = api.dataset.get_info_by_id(g.DATASET_ID)
                used_volumes_names = [volume.name for volume in api.volume.get_list(dataset.id)]

            # DICOM
            for serie_id, files in series_infos.items():
                item_path = files[0]
                if sly.volume.get_extension(path=item_path) is None:
                    sly.logger.warn(
                        f"Can not recognize file extension {item_path}, serie will be skipped"
                    )
                    skipped_series.append(serie_id)
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
                imported_files.extend(files)

            # NRRD
            for nrrd_path in nrrd_paths:
                name = sly.fs.get_file_name_with_ext(path=nrrd_path)
                name = f.generate_free_name(
                    used_names=used_volumes_names, possible_name=name, with_ext=True
                )
                used_volumes_names.append(name)
                g.api.volume.upload_nrrd_serie_path(
                    dataset_id=dataset.id, name=name, path=nrrd_path, log_progress=True
                )
                imported_files.append(nrrd_path)
            api.task.set_output_project(task_id, project.id, project.name)
            if g.DATASET_ID:
                w.workflow_output(api, g.DATASET_ID, "dataset")
            else:
                w.workflow_output(api, project.id, "project")

        if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
            imported_path = g.INPUT_DIR or g.INPUT_FILE
            not_imported_files = _not_imported(downloaded_files, imported_files)
            if len(skipped_series) > 0:
                _keep_source(
                    selected_path,
                    f"{len(skipped_series)} DICOM serie(s) were skipped and not imported: {skipped_series}",
                )
            elif len(not_imported_files) > 0:
                _keep_source(
                    selected_path,
                    f"{len(not_imported_files)} file(s) are not part of any imported volume, "
                    f"e.g. {not_imported_files[:5]}",
                )
            elif selected_path:
                if imported_path != selected_path:
                    sly.logger.info(
                        f"Data was imported from '{imported_path}' (resolved from the selected "
                        f"path '{selected_path}'); only the selected path will be removed."
                    )
                sly.logger.info(f"Removing source from Team Files: '{selected_path}'")
                api.file.remove(team_id=g.TEAM_ID, path=selected_path)
                sly.logger.info(msg=f"Source '{selected_path}' was successfully removed from Team Files.")
            else:
                sly.logger.info("Source removal is enabled, but no input file/folder path was provided.")

    g.my_app.stop()


def _not_imported(downloaded_files, imported_files):
    imported = {os.path.realpath(p) for p in imported_files}
    return [
        p
        for p in downloaded_files
        if os.path.realpath(p) not in imported
        and os.path.basename(p) not in sly.fs.JUNK_FILES
        and "__MACOSX" not in p.split(os.sep)
    ]


def _keep_source(selected_path, reason):
    if g.REMOVE_SOURCE and not g.IS_ON_AGENT:
        sly.logger.warn(
            f"Source '{selected_path}' is kept in Team Files and was NOT removed: {reason}"
        )


def main():
    sly.logger.info(
        "Script arguments", extra={"TEAM_ID": g.TEAM_ID, "WORKSPACE_ID": g.WORKSPACE_ID}
    )
    g.my_app.run(initial_events=[{"command": "import-dicom-volumes"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main, log_for_agent=False)
