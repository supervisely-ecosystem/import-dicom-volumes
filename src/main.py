import os

# import mimetypes
import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g
import json

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
import src.nrrd_encoder as nrrd_encoder
from src.metadata_reader import read_dicom_tags

# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/den-mrt/45130000"


def rescale_slope_intercept(value, slope, intercept):
    return value * slope + intercept


def normalize_volume_meta(meta):
    meta["intensity"]["min"] = rescale_slope_intercept(
        meta["intensity"]["min"],
        meta["rescaleSlope"],
        meta["rescaleIntercept"],
    )

    meta["intensity"]["max"] = rescale_slope_intercept(
        meta["intensity"]["max"],
        meta["rescaleSlope"],
        meta["rescaleIntercept"],
    )

    if "windowWidth" not in meta:
        meta["windowWidth"] = meta["intensity"]["max"] - meta["intensity"]["min"]

    if "windowCenter" not in meta:
        meta["windowCenter"] = meta["intensity"]["min"] + meta["windowWidth"] / 2

    return meta


series_pd = inspect_series(path)
series_infos = json.loads(series_pd.to_json(orient="index"))
for index_str, info in series_infos.items():
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(info["files"])
    volume = reader.Execute()
    volume = sitk.DICOMOrient(volume, "RAS")

    # @TODO: dicom, nifti, nrrd
    volume_info = read_dicom_tags(info["files"][0])

    volume_np = sitk.GetArrayFromImage(volume)
    norm_volume_bytes = nrrd_encoder.encode(
        volume_np,
        header={
            "encoding": "gzip",
            "space": "RAS",
            "space directions": info["axis direction"],
            "space origin": info["image origin"],
        },
        compression_level=1,
    )

    volume_meta = normalize_volume_meta(
        {
            "channelsCount": 1,
            "rescaleSlope": 1,
            "rescaleIntercept": 0,
            **volume_info,
            "intensity": {
                "min": info["min intensity"],
                "max": info["max intensity"],
            },
            "dimensionsIJK": {
                "x": volume_np.shape[0],
                "y": volume_np.shape[1],
                "z": volume_np.shape[2],
            },
            "ACS": "RAS",
            # instead of IJK2WorldMatrix field
            "spacing": info["image spacing"],
            "origin": info["image origin"],
            "directions": info["axis direction"],
        }
    )

    norm_volume_hash = sly.fs.get_bytes_hash(norm_volume_bytes)
    g.api.image._upload_data_bulk(lambda v: v, [(norm_volume_bytes, norm_volume_hash)])

    [volume_result] = g.api.image.upload_volume(
        {
            "datasetId": dataset_info.id,
            "volumes": [
                {
                    "hash": norm_volume_hash,
                    "name": f"{volume_name}.nrrd",
                    "meta": volume_meta,
                },
            ],
        }
    )


# norm_volume_hash = get_bytes_hash(norm_volume_bytes)
#         api.image._upload_data_bulk(
#             lambda v: v, [(norm_volume_bytes, norm_volume_hash)]
#         )

#         [volume_result] = api.image.upload_volume(
#             {
#                 "datasetId": dataset_info.id,
#                 "volumes": [
#                     {
#                         "hash": norm_volume_hash,
#                         "name": f"{volume_name}.nrrd",
#                         "meta": volume_meta, #@TODO: add human readable tags
#                     },
#                 ],
#             }
#         )

#         progress.iter_done_report()

#         progress = sly.Progress(
#             "Import volume slices: {}".format(volume_name), sum(data.shape)
#         )

#         for (plane, dimension) in zip(["sagittal", "coronal", "axial"], data.shape):
#             for i in range(dimension):
#                 try:
#                     normal = {"x": 0, "y": 0, "z": 0}

#                     if plane == "sagittal":
#                         pixel_data = data[i, :, :]
#                         normal["x"] = 1
#                     elif plane == "coronal":
#                         pixel_data = data[:, i, :]
#                         normal["y"] = 1
#                     else:
#                         pixel_data = data[:, :, i]
#                         normal["z"] = 1

#                     img_bytes = nrrd_encoder.encode(
#                         pixel_data, header={"encoding": "gzip"}, compression_level=1
#                     )

#                     img_hash = get_bytes_hash(img_bytes)
#                     api.image._upload_data_bulk(lambda v: v, [(img_bytes, img_hash)])

#                     cur_img = {
#                         "hash": img_hash,
#                         "sliceIndex": i,
#                         "normal": normal,
#                     }

#                     api.image._upload_volume_slices_bulk_add_dict(
#                         volume_result["id"], [cur_img], None
#                     )

#                     images_cnt += 1

#                 except Exception as e:
#                     exc_str = str(e)
#                     sly.logger.warn(
#                         "File skipped due to error: {}".format(exc_str),
#                         exc_info=True,
#                         extra={
#                             "exc_str": exc_str,
#                             "file_path": entry_path,
#                         },
#                     )

#                 progress.iter_done_report()

#     return images_cnt


# import pydicom

# tag = pydicom.tag.Tag(0x10, 0x20)

# # Option 1) Retrieve the keyword:
# keyword = pydicom.datadict.keyword_for_tag(tag)
# # Option 2) Retrieve the complete datadict entry:
# entry = pydicom.datadict.get_entry(tag)
# representation, multiplicity, name, is_retired, keyword = entry


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
