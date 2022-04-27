import supervisely as sly
import src.sly_functions as f
import src.sly_globals as g


sly.logger.info("Application has been started")
print("hey there")


project_name = "test"
dataset_name = "ds-01"

project = g.api.project.get_or_create(
    g.workspace_id, project_name, type=sly.ProjectType.VOLUMES
)
dataset = g.api.dataset.get_info_by_name(project.id, dataset_name)
if dataset is not None:
    g.api.dataset.remove(dataset.id)
dataset = g.api.dataset.get_or_create(project.id, dataset_name)

# path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM"
path = "/Users/max/work/medsi-mrt-duplicate/mrt-2/DICOM/S66420/S1010"
# nifti examples
# path = "/Users/max/work/medsi-mrt-duplicate/nifti"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/nrrd_example"
# path = "/Users/max/work/medsi-mrt-duplicate/den-mrt/45130000"


series_infos = sly.volume.inspect_series(path)

for (files, meta) in series_infos:
    item_path = files[0]
    if sly.volume.get_extension(item_path) is None:
        sly.logger.warn(
            f"Can not recognize file extension {item_path}, serie will be skipped"
        )
        continue
    name = f"{sly.fs.get_file_name(item_path)}.nrrd"
    res = g.api.volume.upload_dicom_serie_paths(dataset.id, name, files, meta)


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


f.shutdown_app()
