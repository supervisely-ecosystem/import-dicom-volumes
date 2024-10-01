import functools
import os
from typing import Callable
import tarfile
import zipfile

import supervisely as sly
from supervisely.io.fs import get_file_ext, get_file_name, get_file_name_with_ext, silent_remove

import sly_globals as g


def get_project_name_from_input_path(input_path: str) -> str:
    """Returns project name from target sly folder name."""

    basename = os.path.basename(input_path)
    if basename == "":
        return None
    return basename


def update_progress(count, api: sly.Api, task_id: int, progress: sly.Progress) -> None:
    count = min(count, progress.total - progress.current)
    progress.iters_done(count)
    if progress.need_report():
        progress.report_progress()


def get_progress_cb(
    api: sly.Api,
    task_id: int,
    message: str,
    total: int,
    is_size: bool = False,
    func: Callable = update_progress,
) -> functools.partial:
    progress = sly.Progress(message, total, is_size=is_size)
    progress_cb = functools.partial(func, api=api, task_id=task_id, progress=progress)
    progress_cb(0)
    return progress_cb


def is_archive(path, local=True):
    if local and tarfile.is_tarfile(path):
        return True
    elif local and zipfile.is_zipfile(path):
        return True
    return get_file_ext(path) in [".zip", ".tar"] or path.endswith(".tar.gz")


def download_data_from_team_files(api: sly.Api, task_id: int, save_path: str) -> str:
    """Download data from remote directory in Team Files."""
    project_path = None
    if not g.IS_ON_AGENT:
        if g.INPUT_DIR or g.INPUT_FILES:
            g.INPUT_DIR = g.INPUT_DIR or g.INPUT_FILES
            listdir = api.file.listdir(g.TEAM_ID, g.INPUT_DIR)
            if len(listdir) == 1 and is_archive(listdir[0], local=False):
                sly.logger.info("Folder mode is selected, but archive file is uploaded.")
                sly.logger.info("Switching to file mode.")
                g.INPUT_DIR, g.INPUT_FILE = None, os.path.join(g.INPUT_DIR, listdir[0])
        elif g.INPUT_FILE or g.INPUT_FILES:
            g.INPUT_FILE = g.INPUT_FILE or g.INPUT_FILES
            if not is_archive(g.INPUT_FILE, local=False):
                sly.logger.info("File mode is selected, but file is not .zip or .tar archive.")
                curr_path = os.path.normpath(g.INPUT_FILE)
                parent_dir = os.path.dirname(curr_path)
                grandparent_dir = os.path.dirname(parent_dir)
                if grandparent_dir == "/import/import-dicom-volumes":
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None
                listdir = api.file.listdir(g.TEAM_ID, parent_dir)
                if all([sly.fs.get_file_ext(f) in [".dcm", ".nrrd", ".dicom"] for f in listdir]):
                    g.INPUT_DIR, g.INPUT_FILE = parent_dir, None

    if g.INPUT_DIR is not None:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(g.INPUT_DIR)
        else:
            cur_files_path = g.INPUT_DIR
        remote_path = g.INPUT_DIR
        project_path = os.path.join(save_path, os.path.basename(os.path.normpath(cur_files_path)))
        sizeb = api.file.get_directory_size(g.TEAM_ID, remote_path)
        progress_cb = get_progress_cb(
            api=api,
            task_id=task_id,
            message=f"Downloading {remote_path.lstrip('/').rstrip('/')}",
            total=sizeb,
            is_size=True,
        )
        api.file.download_directory(
            team_id=g.TEAM_ID,
            remote_path=remote_path,
            local_save_path=project_path,
            progress_cb=progress_cb,
        )
        save_path = project_path

    elif g.INPUT_FILE is not None:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(g.INPUT_FILE)
        else:
            cur_files_path = g.INPUT_FILE
        remote_path = g.INPUT_FILE
        local_save_path = os.path.join(save_path, get_file_name_with_ext(cur_files_path))

        extrack_dir = os.path.join(save_path, get_file_name(cur_files_path))
        sizeb = api.file.get_info_by_path(g.TEAM_ID, remote_path).sizeb
        progress_cb = get_progress_cb(
            api=api,
            task_id=task_id,
            message=f"Downloading {remote_path.lstrip('/')}",
            total=sizeb,
            is_size=True,
        )
        api.file.download(
            team_id=g.TEAM_ID,
            remote_path=remote_path,
            local_save_path=local_save_path,
            progress_cb=progress_cb,
        )
        if is_archive(local_save_path):
            save_archive_path = local_save_path
            sly.fs.unpack_archive(save_archive_path, extrack_dir)
            silent_remove(save_archive_path)
        elif local_save_path.endswith(".nii.gz") or local_save_path.endswith(".nii"):
            file_name = get_file_name_with_ext(local_save_path)
            msg = f"NIfTI files are not supported. Please upload an archive or directory containing .nrrd or .dcm files."
            sly.logger.error(msg, exc_info=False)
            api.task.set_output_error(task_id, msg, description=f"File: {file_name}")
            return None
        elif local_save_path.endswith(".gz") and not is_archive(local_save_path):
            msg = "Unsupported archive format. Please, use .zip, .tar or .tar.gz files."
            sly.logger.error(msg, exc_info=False)
            api.task.set_output_error(task_id, msg, description=f"File: {local_save_path}")
            return None

    return save_path


def generate_free_name(used_names, possible_name, with_ext=False, extend_used_names=False):
    res_name = possible_name
    new_suffix = 1
    while res_name in used_names:
        if with_ext is True:
            res_name = "{}_{:02d}{}".format(
                get_file_name(possible_name),
                new_suffix,
                get_file_ext(possible_name),
            )
        else:
            res_name = "{}_{:02d}".format(possible_name, new_suffix)
        new_suffix += 1
    if extend_used_names:
        used_names.add(res_name)
    return res_name


def get_project_dir(path: str) -> str:
    """Returns project directory."""

    def _volumes_exists(path: str) -> bool:
        """Returns True if path contains volumes."""
        listdir = sly.fs.list_files(path)
        if len([f for f in listdir if sly.volume.get_extension(f) is not None]) > 0:
            return True
        return False

    all_volume_dirs = [d for d in sly.fs.dirs_filter(path, _volumes_exists)]
    if len(all_volume_dirs) == 0:
        return path
    common_prefix = os.path.commonprefix(all_volume_dirs)
    return common_prefix
