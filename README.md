<div align="center" markdown>

<img src="" style="width: 100%;"/>

# Import DICOM Volumes

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Usage">Usage</a> •
  <a href="#how-to-run">How to run</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/import-dicom-volumes)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/import-dicom-volumes)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-dicom-volumes&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-dicom-volumes&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-dicom-volumes&counter=runs&label=runs&123)](https://supervise.ly)

</div>

# Overview

Import volumes in `DICOM` or `NRRD` format without annotations. Files in `DICOM` format will be automatically converted to `NRRD` format during import.

#### Input files structure

Directory name defines project name. All volumes in root directory will be moved to dataset with name: `ds0`. Volumes can be placed in any location inside root directory.
 
```
.
my_volumes_project
├── Chest.nrrd
├── ...
├── MRHead.nrrd
├── 1.2.840.113704.1.111.6000.1606737510.1
│   ├── 0ae345a9-cf0c-4dd7-b5da-6e58f360b59c.dcm
│   └──  0b6a989e-56b8-4e81-98dc-f61ccd05c788.dcm
├── 5f022367-aea6-4d86-b437-50cf9e791dec.dcm
└── my_folder
    ├── CTACardio.nrrd
    ├── MRBrainTumor.nrrd
    └── BaselineVolume.nrrd
```

As a result we will get project `my_volumes_project` with 1 dataset named: `ds0`.

# How to Run

**Step 1.** Add [Import DICOM Volumes](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/import-dicom-volumes) app to your team from Ecosystem

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/import-dicom-volumes" src="https://i.imgur.com/7dfX1s2.png" width="350px" style='padding-bottom: 10px'/>

**Step 2.** Run the application from the context menu of the directory with images on Team Files page

<img src="https://i.imgur.com/0DF8igu.png" width="80%" style='padding-top: 10px'>  

**Step 3.** Select options and press the Run button

<img src="https://i.imgur.com/G6UjpD2.png" width="80%" style='padding-top: 10px'>  

### Demo
Example of uploading a flat set of images:
![](https://i.imgur.com/EkLt9ii.gif)


