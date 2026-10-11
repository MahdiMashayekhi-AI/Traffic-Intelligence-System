# Dataset Documentation

## Sources

This project uses the following external datasets. Dataset files are not included in this repository and must be downloaded separately.

| Dataset | Source | Version / Variant |
|---|---|---|
| UA-DETRAC | [Roboflow Universe](https://universe.roboflow.com/car-plates-hhvk8/ua-detrac-riedy-2v0ie) | `UA-DETRAC.v2-v1 yolov11` |
| CityPersons | [Kaggle](https://www.kaggle.com/datasets/hakurei/citypersons) | Single-class variant (`person`) |

The CityPersons source URL and the exact UA-DETRAC version page should be retained to ensure dataset provenance and licensing information can be verified.

## Licenses

Dataset licenses must be verified from the exact source pages listed above. The license of the dataset itself must not be inferred from the license of the model architecture, annotation format, or hosting platform.

| Dataset | License | Status |
|---|---|---|
| UA-DETRAC | Not yet verified for the exact version | Verification required |
| CityPersons | Not yet verified for the exact downloaded copy | Verification required |

**Important:** Do not redistribute either dataset until the applicable source terms and redistribution permissions have been verified. The license of the code in this repository, if any, does not automatically grant rights to the datasets.

## Layout

```text
data/
├── README.md
├── raw/
│   ├── ua_detrac/
│   └── citypersons/
├── interim/
│   ├── ua_detrac/
│   └── citypersons/
├── processed/
│   ├── train/
│   ├── test/
│   └── valid/
└── manifests/
```

- `raw/`: Downloaded datasets and their initial annotations. In this project, the UA-DETRAC class mapping described below was also applied within this directory.
- `interim/`: Intermediate artifacts created during conversion, validation, or preprocessing.
- `processed/`: Dataset files prepared for model training and evaluation.
- `manifests/`: Metadata describing dataset files, splits, class mappings, and processing provenance.

The directory names above describe the intended organization; the actual contents may vary depending on the dataset and processing stage.

## Lineage

### UA-DETRAC

The original label schema contained eight classes:

`0`, `1`, `2`, `3`, `bus`, `car`, `others`, `van`

The class IDs were consolidated into four target classes **within `raw/`** using the following mapping:

| Original class ID | Target class |
|---|---|
| `0`, `5` | `car` |
| `1`, `7` | `van` |
| `2`, `4` | `bus` |
| `3`, `6` | `others` |

This transformation merges semantically equivalent classes from the original and converted label schemas. The resulting class set is:

`car`, `van`, `bus`, `others`

The mapping above documents the intended transformation. The original-to-target mapping should be checked against the actual label files and the source dataset metadata.

### CityPersons

The CityPersons dataset used in this project was obtained as a single-class variant:

`person`

Its labels are intended for person detection. Any conversion or filtering applied to this variant should be documented in the corresponding processing scripts and manifests.

## Known Limitations

- **CityPersons:** Test annotations are unavailable in the downloaded dataset. Therefore, quantitative test evaluation cannot be performed unless valid test labels are obtained from an authorized source.
- **UA-DETRAC:** The downloaded dataset does not contain a `valid/` split. A validation split must be created separately if required. Its origin and split procedure should be documented to prevent data leakage.

## Important

Dataset files are **not included in this repository**. Users must download the datasets manually from their respective sources and place them in the appropriate directories.

Before training or evaluation, verify that the expected images, annotations, class IDs, and dataset splits are present.

Do not assume that a dataset is licensed for redistribution or commercial use merely because it is publicly downloadable.
