import os

import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g
import SimpleITK as sitk

sly.logger.info("Application has been started")
print("hey there")


project_name = "test"
dataset_name = "ds-02"

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_info_by_name(project.id, dataset_name)
if dataset is not None:
    g.api.dataset.remove(dataset.id)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)

# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# path = "/Users/max/work/dicom-private-test/1.2.840.113704.1.111.6000.1606737510.1"
# nifti examples
# path = "/Users/max/work/medsi-mrt-duplicate/nifti"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/den-mrt/45130000"

# @TODO: volume.upload_np - add progresses
# @TODO: https://simpleitk.org/doxygen/v2_0/html/Python_2DicomSeriesReader2_8py-example.html - reimplement inspect?
# @TODO: https://amberzzzz.github.io/2019/11/11/dicomReader/

# # https://simpleitk.org/doxygen/latest/html/Python_2DicomSeriesReader2_8py-example.html
# reader = sitk.ImageSeriesReader()
# series_found = reader.GetGDCMSeriesIDs(path)
# # Process each Dicom series
# for serie in series_found:
#     print("\nSeries:", serie)
#     # Get the Dicom filename corresponding to the current series
#     dicom_names = reader.GetGDCMSeriesFileNames(path, serie)
#     print("\nFiles in series: ", dicom_names)

series_infos = sly.volume.inspect_series(path)

for serie_id, files in series_infos.items():
    # reader = sitk.ImageSeriesReader()
    # reader.SetFileNames(files)
    # volume = reader.Execute()
    # volume = sitk.DICOMOrient(volume, "RAS")
    # print("origin ", volume.GetOrigin())
    # print("direction ", volume.GetDirection())
    # print("spacing ", volume.GetSpacing())
    # print("size ", volume.GetSize())

    item_path = files[0]
    if sly.volume.get_extension(item_path) is None:
        sly.logger.warn(
            f"Can not recognize file extension {item_path}, serie will be skipped"
        )
        continue

    name = f"{sly.fs.get_file_name(item_path)}.nrrd"
    res = g.api.volume.upload_dicom_serie_paths(dataset.id, name, files, True)
    # TODO: upload dicom tags

f.shutdown_app()
