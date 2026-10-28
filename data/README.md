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
| UA-DETRAC (Roboflow-hosted `UA-DETRAC.v2-v1`) | MIT (stated in the downloaded `data/raw/ua_detrac/README.dataset.txt`) | Partially verified: the Roboflow Universe page was inaccessible (HTTP 403), so the license displayed on the live page could not be independently confirmed. |
| UA-DETRAC (original, University at Albany) | Not specified | Could not be verified from the downloaded copy or the Roboflow page. |
| CityPersons (Kaggle) | Not specified | Kaggle page access was limited and did not expose a license field; could not be verified. |

**Important:** Do not redistribute either dataset until the applicable source terms and redistribution permissions have been verified. The license of the code in this repository, if any, does not automatically grant rights to the datasets.

## Layout

```text
data/
├── README.md
├── raw/
│   ├── ua_detrac/       # split-first layout: train/{images,labels}, test/{images,labels}
│   └── citypersons/     # type-first layout: images/{train,val,test}, labels/{train,val}
├── interim/             # (planned) intermediate artifacts from conversion/preprocessing
├── processed/           # (planned) traffic_v1 dataset prepared for training/evaluation
│   ├── train/
│   ├── test/
│   └── valid/
└── manifests/           # (planned) metadata describing files, splits, class mappings, provenance
```

- `raw/`: Downloaded datasets and their initial annotations. **Must not be modified or overwritten.** In this project, the UA-DETRAC class mapping described below was applied within this directory.
- `interim/`: Planned directory for intermediate artifacts created during conversion, validation, or preprocessing. Not yet populated.
- `processed/`: Planned directory for dataset files prepared for model training and evaluation. The `traffic_v1` dataset is planned here but does not yet exist.
- `manifests/`: Planned directory for metadata describing dataset files, splits, class mappings, and processing provenance.

Directories marked **(planned)** do not yet exist on disk; only `data/raw/` contains downloaded data.

## Lineage

### UA-DETRAC

The original label schema contained eight classes:

`0`, `1`, `2`, `3`, `bus`, `car`, `others`, `van`

The class IDs were consolidated into four target classes **within `raw/`** using the mapping documented in the legacy script (not in the repo) `scratch/old_scripts/veh_merge_classes.py`:

| Original class ID | Target class |
|---|---|
| `0`, `5` | `car` |
| `1`, `7` | `van` |
| `2`, `4` | `bus` |
| `3`, `6` | `others` |

Verified merged class counts (training labels, `data/raw/ua_detrac/train/labels`):
- `car` (classes `{0, 5}` merged): 222,021 instances
- `van` (classes `{1, 7}` merged): 21,511 instances
- `bus` (classes `{2, 4}` merged): 21,295 instances
- `others` (classes `{3, 6}` merged): 1,289 instances

The resulting merged class set is: `car`, `van`, `bus`, `others`. Class ID `2` (bus originals) is retained as `bus` after merging; no original class ID is dropped except via the mapping above.

Note: seven car instances are missing relative to the expected original totals (classes `{0, 5}` sum to 222,028, but the merged `car` count is 222,021). This discrepancy is documented as unresolved in `docs/data/dataset_audit.md` because the original Roboflow labels could not be downloaded (HTTP 403).

### CityPersons

The CityPersons dataset used in this project was obtained as a single-class variant (`person`).

Verified raw label class IDs (`count_instances` on `data/raw/citypersons/labels/`):
- `train`: `{4: 20974}`
- `val`: `{4: 4153}`

The raw labels use class ID `4`, while `data/raw/citypersons/data.yaml` declares `names: {0: person}`. The legacy script (not in the repo) `scratch/old_scripts/ped_change_dataset_class.py` explains the discrepancy: it rewrites every label's class to `"4"`. The raw class-ID `4` must therefore be remapped to `0` (`person`) when building the `traffic_v1` dataset.

Verified instance counts (raw labels): train 20,974 person instances; val 4,153 person instances.

## Known Limitations

- **CityPersons:** Test annotations are unavailable in the downloaded dataset (1,525 test images, 0 label files). Quantitative test evaluation cannot be performed unless valid test labels are obtained from an authorized source.
- **UA-DETRAC:** The downloaded dataset does not contain a `valid/` split. A validation split must be created separately if required. Its origin and split procedure should be documented to prevent data leakage.
- **UA-DETRAC sequence separation:** Verified filename-pattern parsing (`MVI_<sequence_id>_frame<frame_number>_jpg.rf.<hash>.jpg`) shows 32 unique sequence IDs in training and 13 in testing, with no sequence overlap between the two splits. Sequence-level separation matters because frames from the same video sequence are highly correlated; placing frames from one sequence in both train and test would leak information and overstate generalization performance. Future splits must be grouped by sequence ID.
- **UA-DETRAC missing car instances:** Seven car instances are unaccounted for after class merging (documented as unresolved in `docs/data/dataset_audit.md`).

## Important

Dataset files are **not included in this repository**. Users must download the datasets manually from their respective sources and place them in the appropriate directories.

Before training or evaluation, verify that the expected images, annotations, class IDs, and dataset splits are present.

Do not assume that a dataset is licensed for redistribution or commercial use merely because it is publicly downloadable.
