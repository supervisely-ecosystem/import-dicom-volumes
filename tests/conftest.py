"""Offline test harness: a fake `sly_globals` module and a small in-memory fake Supervisely API.

Nothing here talks to a Supervisely server. The app code is imported from ../src
(or from $APP_SRC, which lets the same tests run against an older checkout).
DICOM series are real files written with SimpleITK/pydicom (SDK dependencies), so
series detection runs through the real sly.volume.inspect_dicom_series (GDCM).

Run:  pip install -r dev_requirements.txt pytest && python -m pytest tests
"""

import os
import shutil
import sys
import types

import pytest

SRC = os.environ.get(
    "APP_SRC", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)
SRC = os.path.abspath(SRC)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import supervisely as sly  # noqa: E402
from supervisely.volume.volume import ALLOWED_VOLUME_EXTENSIONS  # noqa: E402


class FakeMyApp:
    def __init__(self):
        self.stopped = False

    def callback(self, name):
        return lambda fn: fn

    def stop(self, *args, **kwargs):
        self.stopped = True


def _make_fake_globals():
    """sly_globals.py creates a real Api/AppService at import time; use a stand-in."""
    g = types.ModuleType("sly_globals")
    g.my_app = FakeMyApp()
    g.ALLOWED_VOLUME_EXTENSIONS = ALLOWED_VOLUME_EXTENSIONS
    g.DEFAULT_DATASET_NAME = "ds0"
    return g


sys.modules["sly_globals"] = _make_fake_globals()


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeFileApi:
    """Team Files as a dict {"/abs/path/file": bytes}; directories are implicit."""

    def __init__(self, files):
        self.files = dict(files)
        self.removed = []

    @staticmethod
    def _dir_prefix(path):
        return path.rstrip("/") + "/"

    def listdir(self, team_id, path, recursive=False):
        prefix = self._dir_prefix(path)
        out = set()
        for p in self.files:
            if p.startswith(prefix):
                out.add(prefix + p[len(prefix) :].split("/")[0])
        return sorted(out)

    def get_directory_size(self, team_id, path):
        prefix = self._dir_prefix(path)
        return sum(len(v) for p, v in self.files.items() if p.startswith(prefix))

    def download_directory(self, team_id, remote_path, local_save_path, progress_cb=None):
        prefix = self._dir_prefix(remote_path)
        for p, data in self.files.items():
            if p.startswith(prefix):
                dst = os.path.join(local_save_path, p[len(prefix) :])
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as fh:
                    fh.write(data)

    def get_info_by_path(self, team_id, path):
        return Obj(sizeb=len(self.files[path]))

    def download(self, team_id, remote_path, local_save_path, cache=None, progress_cb=None):
        os.makedirs(os.path.dirname(local_save_path), exist_ok=True)
        with open(local_save_path, "wb") as fh:
            fh.write(self.files[remote_path])

    def is_on_agent(self, path):
        return False

    def remove(self, team_id, path):
        self.removed.append(path)
        prefix = self._dir_prefix(path)
        for p in list(self.files):
            if p == path or p.startswith(prefix):
                del self.files[p]


class FakeTaskApi:
    def __init__(self):
        self.errors = []
        self.output_projects = []

    def set_output_error(self, task_id, title, description=None, *a, **kw):
        self.errors.append(title)

    def set_output_project(self, task_id, project_id, project_name=None, *a, **kw):
        self.output_projects.append(project_id)


class FakeProjectApi:
    def create(self, workspace_id, name, type=None, change_name_if_conflict=False, **kw):
        return Obj(id=100, name=name)

    def get_info_by_id(self, project_id):
        return Obj(id=project_id, name="existing")


class FakeDatasetApi:
    def create(self, project_id, name, change_name_if_conflict=False, **kw):
        return Obj(id=1000, name=name)


class FakeVolumeApi:
    def __init__(self):
        self.uploaded = []

    def upload_dicom_serie_paths(self, dataset_id, name, paths, log_progress=True, anonymize=True):
        self.uploaded.append(name)

    def upload_nrrd_serie_path(self, dataset_id, name, path, log_progress=True):
        self.uploaded.append(name)


class FakeApi:
    def __init__(self, files):
        self.file = FakeFileApi(files)
        self.task = FakeTaskApi()
        self.project = FakeProjectApi()
        self.dataset = FakeDatasetApi()
        self.volume = FakeVolumeApi()


def _write_series(out_dir, series_uid, n, raw):
    """Writes a real n-slice DICOM series. raw=True: no Part-10 preamble and no file
    extension (legacy ACR-NEMA style) - GDCM finds the series, but the SDK's
    get_extension() cannot classify it, so the app skips it."""
    import pydicom
    import SimpleITK as sitk
    from pydicom.filebase import DicomBytesIO

    os.makedirs(out_dir, exist_ok=True)
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()
    result = {}
    for i in range(n):
        img = sitk.Image(4, 4, sitk.sitkInt16)
        tags = {
            "0020|000e": series_uid,
            "0020|000d": series_uid + ".0",
            "0008|0060": "CT",
            "0020|0013": str(i + 1),
            "0020|0032": "0\\0\\{}".format(i),
            "0020|0037": "1\\0\\0\\0\\1\\0",
            "0008|0018": "{}.{}".format(series_uid, i + 1),
        }
        for k, v in tags.items():
            img.SetMetaData(k, v)
        path = os.path.join(out_dir, "s{}.dcm".format(i))
        writer.SetFileName(path)
        writer.Execute(img)
        if raw:
            ds = pydicom.dcmread(path)
            ds.decode()
            fp = DicomBytesIO()
            fp.is_little_endian, fp.is_implicit_VR = True, True
            pydicom.filewriter.write_dataset(fp, ds)
            result["IM{:04d}".format(i)] = fp.getvalue()
        else:
            with open(path, "rb") as fh:
                result["s{}.dcm".format(i)] = fh.read()
    return result


@pytest.fixture(scope="session")
def dicom(tmp_path_factory):
    """dicom(uid, n=3, raw=False) -> {file_name: bytes} of a real DICOM series."""
    base = tmp_path_factory.mktemp("dicom_src")
    cache = {}

    def make(uid, n=3, raw=False):
        key = (uid, n, raw)
        if key not in cache:
            cache[key] = _write_series(str(base / "{}_{}_{}".format(uid, n, raw)), uid, n, raw)
        return cache[key]

    return make


@pytest.fixture
def run_app(tmp_path, monkeypatch):
    """run(files, folder=None, file=None, dnd=None) -> FakeApi after one app run."""
    import main
    import sly_functions  # noqa: F401

    g = sys.modules["sly_globals"]

    def run(files, folder=None, file=None, dnd=None):
        api = FakeApi(files)
        storage = tmp_path / "app_data"
        if storage.exists():
            shutil.rmtree(storage)
        storage.mkdir()
        app = FakeMyApp()
        for name, value in {
            "api": api,
            "my_app": app,
            "TASK_ID": 1,
            "TEAM_ID": 7,
            "WORKSPACE_ID": 9,
            "PROJECT_ID": None,
            "DATASET_ID": None,
            "INPUT_DIR": folder,
            "INPUT_FILE": file,
            "INPUT_FILES": dnd,
            "OUTPUT_PROJECT_NAME": "",
            "REMOVE_SOURCE": True,
            "ANONYMIZE_VOLUMES": True,
            "IS_ON_AGENT": False,
            "STORAGE_DIR": str(storage),
        }.items():
            monkeypatch.setattr(g, name, value, raising=False)
        monkeypatch.setattr(main.w, "workflow_output", lambda *a, **kw: None)
        main.import_dicom_volumes(api, 1, {}, {}, None)
        api.app_stopped = app.stopped
        return api

    return run
