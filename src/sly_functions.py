import functools
import os
import shutil
from typing import Callable
import tarfile
import zipfile

import supervisely as sly
from supervisely.io.fs import (get_file_ext, get_file_name,
                               get_file_name_with_ext, silent_remove)

import sly_globals as g


def get_project_name_from_input_path(input_path: str) -> str:
    """Returns project name from target sly folder name."""
    return os.path.basename(input_path)


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


def download_data_from_team_files(api: sly.Api, task_id: int, save_path: str) -> str:
    """Download data from remote directory in Team Files."""
    project_path = None
    if g.INPUT_DIR:
        listdir = api.file.listdir(g.TEAM_ID, g.INPUT_DIR)
        if len(listdir) == 1 and sly.fs.get_file_ext(listdir[0]) in [".zip", ".tar"]:
            sly.logger.info("Folder mode is selected, but archive file is uploaded.")
            sly.logger.info("Switching to file mode.")
            g.INPUT_DIR, g.INPUT_FILE = None, os.path.join(g.INPUT_DIR, listdir[0])
    elif g.INPUT_FILE:
        if sly.fs.get_file_ext(g.INPUT_FILE) not in [".zip", ".tar"]:
            curr_path = g.INPUT_FILE
            parent_dir = os.path.dirname(curr_path)
            grandparent_dir = os.path.dirname(parent_dir)
            while grandparent_dir != "/import/import-dicom-volumes":
                curr_path = os.path.dirname(curr_path)
                parent_dir = os.path.dirname(curr_path)
                grandparent_dir = os.path.dirname(parent_dir)
            if not parent_dir.endswith("/"):
                parent_dir += "/"
            listdir = api.file.listdir(g.TEAM_ID, parent_dir)
            if len(listdir) > 1:
                curr_path = parent_dir
            elif len(listdir) == 1 and api.file.exists(g.TEAM_ID, curr_path):
                curr_path = parent_dir
            if not curr_path.endswith("/"):
                curr_path += "/"
            sly.logger.info(f"project_dir: {curr_path}")
            sly.logger.info("File mode is selected, but directory is uploaded.")
            sly.logger.info("Switching to folder mode.")
            g.INPUT_DIR, g.INPUT_FILE = curr_path, None
        
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

    elif g.INPUT_FILE is not None:
        if g.IS_ON_AGENT:
            agent_id, cur_files_path = api.file.parse_agent_id_and_path(g.INPUT_FILE)
        else:
            cur_files_path = g.INPUT_FILE
        remote_path = g.INPUT_FILE
        save_archive_path = os.path.join(save_path, get_file_name_with_ext(cur_files_path))
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
            local_save_path=save_archive_path,
            progress_cb=progress_cb,
        )
        if not get_file_ext(save_archive_path) in [".zip", ".tar"]:
            g.my_app.logger.error("Unsupported archive extension. Supported extensions: zip, tar")  
            raise Exception("Unsupported archive extension. Supported extensions: zip, tar")
        shutil.unpack_archive(save_archive_path, extrack_dir)
        silent_remove(save_archive_path)
        sly.fs.remove_junk_from_dir(save_path)
        dir_list = os.listdir(save_path)
        if len(dir_list) != 1:          
            g.my_app.logger.error("The archive should contain only 1 project directory at the root level")
            raise Exception("The archive should contain only 1 project directory at the root level")
        if not os.path.isdir(os.path.join(save_path, dir_list[0])):
            g.my_app.logger.error("The archive should contain only the project directory at the root level")
            raise Exception("The archive should contain only the project directory at the root level")

        project_name = dir_list[0]
        project_path = os.path.join(save_path, project_name)
    return project_path


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
