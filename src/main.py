import supervisely as sly
import shutil, os
from supervisely.io.fs import silent_remove
from distutils.util import strtobool

from supervisely.io.fs import mkdir

from dotenv import load_dotenv


load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()

INPUT_DIR: str = os.environ.get("modal.state.slyFolder", None)
INPUT_FILE: str = os.environ.get("modal.state.slyFile", None)

if INPUT_DIR:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
else:
    IS_ON_AGENT = api.file.is_on_agent(INPUT_FILE)

OUTPUT_PROJECT_NAME = os.environ.get("modal.state.project_name", "")
REMOVE_SOURCE = bool(strtobool(os.getenv("modal.state.remove_source")))

DEFAULT_DATASET_NAME = "ds0"
ANONYMIZE_VOLUMES = bool(strtobool(os.getenv("modal.state.anonymizeVolumes")))

STORAGE_DIR: str = sly.app.get_data_dir()
mkdir(STORAGE_DIR, True)


class MyImport(sly.app.Import):
    def process(self, context: sly.app.Import.Context):

        project_dir = context.path
        if context.is_directory is False:
            shutil.unpack_archive(project_dir, STORAGE_DIR)
            silent_remove(project_dir)
            project_name = os.listdir(STORAGE_DIR)[0]
            if len(os.listdir(STORAGE_DIR)) > 1:
                raise Exception("There must be only 1 project directory in the archive")
            project_dir = os.path.join(STORAGE_DIR, project_name)
        else:
            project_name = os.path.basename(project_dir)

        project = api.project.create(
            workspace_id=context.workspace_id,
            name=project_name,
            type=sly.ProjectType.VOLUMES,
            change_name_if_conflict=True,
        )
        dataset = api.dataset.create(
            project_id=project.id, name=DEFAULT_DATASET_NAME, change_name_if_conflict=True
        )

        # DICOM
        series_infos = sly.volume.inspect_dicom_series(root_dir=project_dir)
        for serie_id, files in series_infos.items():
            item_path = files[0]
            if sly.volume.get_extension(path=item_path) is None:
                sly.logger.warn(
                    f"Can not recognize file extension {item_path}, serie will be skipped"
                )
                continue
            name = f"{sly.fs.get_file_name(path=item_path)}.nrrd"
            api.volume.upload_dicom_serie_paths(
                dataset_id=dataset.id,
                name=name,
                paths=files,
                log_progress=True,
                anonymize=ANONYMIZE_VOLUMES,
            )

        # NRRD
        nrrd_paths = sly.volume.inspect_nrrd_series(root_dir=project_dir)
        for nrrd_path in nrrd_paths:
            name = sly.fs.get_file_name_with_ext(path=nrrd_path)
            api.volume.upload_nrrd_serie_path(
                dataset_id=dataset.id, name=name, path=nrrd_path, log_progress=True
            )

        if REMOVE_SOURCE and not IS_ON_AGENT:
            sly.logger.info(f"7777777777777777777777777777777     {INPUT_DIR}")
            sly.logger.info(f"7777777777777777777777777777777     {project_dir}")
            api.file.remove(team_id=context.team_id, path=INPUT_DIR)
            source_dir_name = INPUT_DIR.lstrip("/").rstrip("/")
            sly.logger.info(msg=f"Source directory: '{source_dir_name}' was successfully removed.")


app = MyImport()
app.run()
