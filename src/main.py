import os

import magic

# import mimetypes
import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g

# https://github.com/InsightSoftwareConsortium/SimpleITK-Notebooks/blob/master/Python/characterize_data.py
# from src.volume_reader import process_file
# from supervisely.volume.parsers import dicom

# @TODO: new project / append to existing project
# @TODO: test nrrd and nifty
# @TODO: https://pydicom.github.io/pydicom/dev/auto_examples/image_processing/reslice.html
# @TODO: https://simpleitk.readthedocs.io/en/master/link_DicomSeriesReader_docs.html
# @TODO: reoriented = sitk.DICOMOrient(img, 'RAS')

import SimpleITK as sitk

from src.dicom_helper import inspect_series

path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/den-mrt/45130000"

res = inspect_series(path)
for col in res.columns:
    print(col)
# files
# MD5 intensity hash
# image size
# image spacing
# image origin
# axis direction
# pixel type
# min intensity
# max intensity

print(res[:5])

# len(res.iloc[0]['files'])

reader = sitk.ImageSeriesReader()
dicom_names = reader.GetGDCMSeriesFileNames(path)
reader.SetFileNames(dicom_names)

image = reader.Execute()
size = image.GetSize()
print("Image size:", size[0], size[1], size[2])

# import pydicom as dicom

# reader = sitk.ImageFileReader()
# reader.SetFileName(dicom_names[0])
# reader.LoadPrivateTagsOn()
# reader.ReadImageInformation()
# reader.GetMe
# for k in reader.GetMetaDataKeys():
#     v = reader.GetMetaData(k)
#     print(f'({k}) = = "{v}"')
# https://stackoverflow.com/questions/66609095/convert-dicom-tag-into-something-more-readable

raise RuntimeError(123)

sly.logger.info("Application has been started")
print("hey there")


project_name = "test"
dataset_name = "ds-01"

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)


# total_counter = 0
# for root, dirs, files in os.walk(path):
#     dir_has_dcm_files = False

#     for entry_name in files:
#         full_entry_name = os.path.join(root, entry_name)
#         entry_mime = magic.from_file(full_entry_name, mime=True)

#         if entry_mime == "application/dicom":
#             dir_has_dcm_files = True

#         # entry_name_low = entry_name.lower()
#         # if entry_name_low.endswith("nrrd") or entry_name_low.endswith("nrrd.gz"):
#         #     parser_type = "nrrd"
#         # elif entry_name_low.endswith("nii") or entry_name_low.endswith("nii.gz"):
#         #     parser_type = "nifti"
#         # elif entry_name_low.endswith("dcm"):
#         #     dir_has_dcm_files = True
#         # else:
#         #     pass
#         # if parser_type is not None:
#         #     total_counter += process_file(
#         #         g.api, project, dataset, full_entry_name, parser_type
#         #     )
#         # else:
#         #     raise NotImplementedError("file without extension")

#     if dir_has_dcm_files:
#         total_counter += process_file(g.api, project, dataset, root, "dicom")

f.shutdown_app()
