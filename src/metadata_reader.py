import SimpleITK as sitk
import pydicom as dicom
import stringcase
from typing import List, Union

# from pydicom.valuerep import MultiValue

photometricInterpretationRGB = set(
    [
        "RGB",
        "PALETTE COLOR",
        "YBR_FULL",
        "YBR_FULL_422",
        "YBR_PARTIAL_422",
        "YBR_PARTIAL_420",
        "YBR_RCT",
    ]
)


def read_dicom_tags(path, allowed_keys: Union[None, List[str]] = None):
    # allowed_keys = [
    #     "SeriesInstanceUID",
    #     "Modality",
    #     "PatientID",
    #     "PatientName",
    #     "WindowCenter",
    #     "WindowWidth",
    #     "RescaleIntercept",
    #     "RescaleSlope",
    #     "PhotometricInterpretation",
    # ]
    reader = sitk.ImageFileReader()
    reader.SetFileName(path)
    reader.LoadPrivateTagsOn()
    reader.ReadImageInformation()

    vol_info = {}
    for k in reader.GetMetaDataKeys():
        v = reader.GetMetaData(k)
        tag = dicom.tag.Tag(k.split("|")[0], k.split("|")[1])
        keyword = dicom.datadict.keyword_for_tag(tag)
        keyword = stringcase.camelcase(keyword)
        if allowed_keys is not None and keyword not in allowed_keys:
            continue
        vol_info[keyword] = v
        if keyword in [
            "windowCenter",
            "windowWidth",
            "rescaleIntercept",
            "rescaleSlope",
        ]:
            vol_info[keyword] = float(vol_info[keyword])
        elif (
            keyword == "photometricInterpretation" and v in photometricInterpretationRGB
        ):
            vol_info["channelsCount"] = 3
    return vol_info
