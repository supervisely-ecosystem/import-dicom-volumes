import os
import supervisely

from supervisely.volume.parsers import dicom, nrrd, nifti
from supervisely.volume.nrrd_encoder import encoder as nrrd_encoder
from supervisely.io import fs
import numpy as np


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


def process_file(api, project_info, dataset_info, entry_path, parser_type):
    def_volume_name = fs.get_file_name(entry_path)
    # def_volume_name = os.path.relpath(
    #     os.path.splitext(entry_path)[0], TaskPaths.DATA_DIR
    # ).replace(os.sep, "__")

    volumes = []
    images_cnt = 0

    if parser_type == "dicom":
        volumes = dicom.load(entry_path)
    elif parser_type == "nrrd":
        volumes = nrrd.load(entry_path)
    elif parser_type == "nifti":
        volumes = nifti.load(entry_path)

    for (volume_name, volume, volume_info) in volumes:
        if volume_name is None:
            volume_name = def_volume_name

        volume.system = "RAS"

        data = volume.aligned_data
        min_max = [int(np.amin(data)), int(np.amax(data))]

        volume_meta = normalize_volume_meta(
            {
                "channelsCount": 1,
                "rescaleSlope": 1,
                "rescaleIntercept": 0,
                **volume_info,
                "intensity": {
                    "min": min_max[0],
                    "max": min_max[1],
                },
                "dimensionsIJK": {
                    "x": data.shape[0],
                    "y": data.shape[1],
                    "z": data.shape[2],
                },
                "ACS": volume.system,
                "IJK2WorldMatrix": volume.aligned_transformation.flatten().tolist(),
            }
        )

        # to save normalized volume
        # from src.loaders import nrrd as nrrd_loader
        # nrrd_loader.save_volume('/sly_task_data/volume.nrrd', volume, src_order=False, src_system=False)

        progress = sly.Progress("Import volume: {}".format(volume_name), 1)

        norm_volume_bytes = nrrd_encoder.encode(
            data,
            header={
                "encoding": "gzip",
                "space": volume.system.upper(),
                "space directions": volume.aligned_transformation[:3, :3].T.tolist(),
                "space origin": volume.aligned_transformation[:3, 3].tolist(),
            },
            compression_level=1,
        )

        norm_volume_hash = fs.get_bytes_hash(norm_volume_bytes)
        api.image._upload_data_bulk(
            lambda v: v, [(norm_volume_bytes, norm_volume_hash)]
        )

        [volume_result] = api.image.upload_volume(
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

        progress.iter_done_report()

        progress = supervisely.Progress(
            "Import volume slices: {}".format(volume_name), sum(data.shape)
        )

        for (plane, dimension) in zip(["sagittal", "coronal", "axial"], data.shape):
            for i in range(dimension):
                try:
                    normal = {"x": 0, "y": 0, "z": 0}

                    if plane == "sagittal":
                        pixel_data = data[i, :, :]
                        normal["x"] = 1
                    elif plane == "coronal":
                        pixel_data = data[:, i, :]
                        normal["y"] = 1
                    else:
                        pixel_data = data[:, :, i]
                        normal["z"] = 1

                    img_bytes = nrrd_encoder.encode(
                        pixel_data, header={"encoding": "gzip"}, compression_level=1
                    )

                    img_hash = fs.get_bytes_hash(img_bytes)
                    api.image._upload_data_bulk(lambda v: v, [(img_bytes, img_hash)])

                    cur_img = {
                        "hash": img_hash,
                        "sliceIndex": i,
                        "normal": normal,
                    }

                    api.image._upload_volume_slices_bulk_add_dict(
                        volume_result["id"], [cur_img], None
                    )

                    images_cnt += 1

                except Exception as e:
                    exc_str = str(e)
                    supervisely.logger.warn(
                        "File skipped due to error: {}".format(exc_str),
                        exc_info=True,
                        extra={
                            "exc_str": exc_str,
                            "file_path": entry_path,
                        },
                    )

                progress.iter_done_report()

    return images_cnt
