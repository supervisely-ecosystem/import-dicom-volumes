"""The source in Team Files must be removed only after a complete import, and only the
path the user selected. Each test reproduces one data-loss scenario from the 2026-10
ecosystem security audit (section 2.2), plus the normal success cases."""

import io
import zipfile


def under(root, named_files):
    return {"{}/{}".format(root.rstrip("/"), n): b for n, b in named_files.items()}


# --- normal case: unchanged behaviour ---------------------------------------------


def test_success_folder_removes_selected_folder(run_app, dicom):
    files = under("/data/study", dicom("1.2.826.1"))
    files["/data/study/vol.nrrd"] = b"NRRD0004\n"
    files["/data/keep_me.txt"] = b"unrelated"
    api = run_app(files, folder="/data/study/")
    assert api.task.errors == []
    assert sorted(api.volume.uploaded) == ["1.2.826.1.nrrd", "vol.nrrd"]
    assert api.file.removed == ["/data/study/"]
    assert set(api.file.files) == {"/data/keep_me.txt"}
    assert api.app_stopped


def test_success_drag_and_drop_removes_only_app_upload_folder(run_app, dicom):
    up = "/import/import-dicom-volumes/42/"
    files = under(up + "scan", dicom("1.2.826.1"))
    files["/import/import-dicom-volumes/41/other.dcm"] = b"another user's upload"
    api = run_app(files, dnd=up)
    assert api.task.errors == []
    assert api.file.removed == [up]
    assert set(api.file.files) == {"/import/import-dicom-volumes/41/other.dcm"}


def test_success_archive_removes_selected_archive(run_app, dicom):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in dicom("1.2.826.1").items():
            z.writestr("study/" + name, data)
    files = {"/data/study.zip": buf.getvalue(), "/data/keep_me.txt": b"unrelated"}
    api = run_app(files, file="/data/study.zip")
    assert api.task.errors == []
    assert api.volume.uploaded == ["1.2.826.1.nrrd"]
    assert api.file.removed == ["/data/study.zip"]
    assert set(api.file.files) == {"/data/keep_me.txt"}


# --- loss scenario 1: nothing found -> error, but the source was still removed ----


def test_nothing_found_keeps_source(run_app):
    """PNG / NIfTI folders inspect as empty; old code set the error and then deleted them."""
    files = {
        "/data/mri/brain.nii.gz": b"\x1f\x8b nifti",
        "/data/mri/slice_001.png": b"\x89PNG",
    }
    api = run_app(files, folder="/data/mri/")
    assert api.task.errors, "the app must report an error"
    assert api.file.removed == []
    assert set(api.file.files) == set(files)
    assert api.app_stopped


# --- loss scenario 2: some found series are skipped -> deleted without import -------


def test_skipped_unclassified_series_keeps_source(run_app, dicom):
    """A legacy DICOM series (no preamble, no extension) is found by GDCM but skipped by
    the app (`continue`); old code imported the other series and deleted both."""
    files = under("/data/study", dicom("1.2.826.1"))
    files.update(under("/data/study", dicom("1.2.826.2", raw=True)))
    api = run_app(files, folder="/data/study/")
    assert api.volume.uploaded == ["1.2.826.1.nrrd"]
    assert api.file.removed == []
    assert "/data/study/IM0000" in api.file.files


def test_files_outside_detected_project_dir_keep_source(run_app, dicom):
    """get_project_dir() narrows the import to folders with classifiable volumes, so the
    legacy series in a sibling folder is never even inspected; old code deleted it."""
    files = under("/data/study/a", dicom("1.2.826.1"))
    files.update(under("/data/study/legacy", dicom("1.2.826.2", raw=True)))
    api = run_app(files, folder="/data/study/")
    assert api.volume.uploaded == ["1.2.826.1.nrrd"]
    assert api.file.removed == []
    assert "/data/study/legacy/IM0000" in api.file.files


def test_mixed_folder_unsupported_files_keep_source(run_app, dicom):
    """A NIfTI next to a DICOM series is not imported; old code deleted it."""
    files = under("/data/study", dicom("1.2.826.1"))
    files["/data/study/brain.nii.gz"] = b"\x1f\x8b nifti"
    api = run_app(files, folder="/data/study/")
    assert api.volume.uploaded == ["1.2.826.1.nrrd"]
    assert api.file.removed == []
    assert "/data/study/brain.nii.gz" in api.file.files


# --- loss scenario 3: re-pointed parent folder is removed ----------------------------


def test_selected_file_does_not_remove_parent_folder(run_app, dicom):
    """Selecting one .dcm re-points INPUT_DIR to its parent folder; old code removed the
    whole parent folder, which the user never selected."""
    files = under("/data/scans", dicom("1.2.826.1"))
    api = run_app(files, file="/data/scans/s0.dcm")
    assert api.task.errors == []
    assert api.volume.uploaded == ["1.2.826.1.nrrd"]
    assert api.file.removed == ["/data/scans/s0.dcm"]
    assert "/data/scans/s1.dcm" in api.file.files
    assert "/data/scans/s2.dcm" in api.file.files
