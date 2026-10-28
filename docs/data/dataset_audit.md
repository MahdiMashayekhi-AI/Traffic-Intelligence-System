# Raw Dataset Audit

## Summary

The raw UA-DETRAC and CityPersons datasets were audited for image-label matching, label validity, class distribution, potential train/test leakage, filename patterns, and image dimensions. Verified findings: CityPersons raw labels use class ID `4` while its `data.yaml` declares `0: person`; the current CityPersons validation snapshot has 500 images and 500 labels with **zero** images without labels (the earlier committed audit's count of 2 is stale); UA-DETRAC contains no duplicate `(sequence_id, frame_number)` pairs in either split; UA-DETRAC train (32 sequences) and test (13 sequences) share no sequence IDs. The loss of seven car instances during UA-DETRAC class merging remains **unresolved** because the Roboflow source is not accessible without an API key (403 Forbidden).

## Findings

| # | Issue | Evidence | Decision |
|---|---|---|---|
| 1 | CityPersons raw class IDs vs. `data.yaml` | `count_instances` on `data/raw/citypersons/labels/train` → `{4: 20974}`; on `.../labels/val` → `{4: 4153}`. Sample label line: `4 0.635986...`. `data/raw/citypersons/data.yaml` declares `names: {0: person}`. Legacy script `scratch/old_scripts/ped_change_dataset_class.py` rewrites every class to `"4"`. | Document the discrepancy: raw labels use class ID `4`, YAML maps `0: person`. The class conversion history (legacy script rewriting all classes to `4`) explains why raw labels contain `4`. |
| 2 | CityPersons validation images without labels | `get_split_dirs` + `match_images_to_labels` on `data/raw/citypersons` (type-first, val): 500 images, 500 labels, `images_without_label = []` (0). The prior committed audit recorded 2 without labels, but those are not present in the current data snapshot. | No images are currently without labels in the val split. Policy recorded: any val image without a label is excluded from the future `traffic_v1` dataset. |
| 3 | UA-DETRAC car instance count mismatch (7 missing) | Merged training car count = 222,021. Expected original classes `{0, 5}` sum = 40,515 + 181,513 = 222,028. Difference = 7 instances. Original Roboflow dataset could not be downloaded (403 Forbidden, requires API key). | **Unresolved.** Original labels unavailable for comparison. Root cause cannot be established from available evidence. |
| 4 | Potential train/test leakage in UA-DETRAC | Train: 32 unique sequence IDs; test: 13 unique sequence IDs; shared IDs: 0. Filename pattern `MVI_<sequence>_frame<frame>_jpg.rf.<hash>.jpg` parsed with `re` named groups. | The sequence-level split is separated with no shared sequence IDs. No duplication detected; this inspection does not prove the entire dataset is free of duplicates, but no evidence of leakage was found. |
| 5 | UA-DETRAC duplicate-frame / augmentation check | Train: 34,374 images, 34,374 unique `(sequence_id, frame_number)` pairs, 0 additional, 0 unparseable. Test: 15,292 images, 15,292 unique pairs, 0 additional, 0 unparseable. | No duplicate sequence/frame pairs were detected in either split; no evidence of augmentation-derived duplicates. |
| 6 | Image dimensions | UA-DETRAC train: 34,374 images at 960 × 540; UA-DETRAC test: 15,292 images at 960 × 540; CityPersons train: 2,975 images at 2048 × 1024; CityPersons val: 500 images at 2048 × 1024; CityPersons test: 1,525 images at 2048 × 1024. | Record as baseline for EDA and preprocessing. |
| 7 | Empty labels in CityPersons | Train: 486 empty label files; val: 61 empty label files. No invalid label lines were reported. | Retain empty labels as background samples. Limitation: regions ignored by the annotation protocol may contain pedestrians that are not labeled (verified annotation format: YOLO `class x y w h`; empty files contain no box lines). |
| 8 | UA-DETRAC label class mapping | The merged dataset uses four classes: `car`, `van`, `bus`, `others`. Original IDs merged: `{0, 5} → car`, `{1, 7} → van`, `{2, 4} → bus`, `{3, 6} → others` (legacy `scratch/old_scripts/veh_merge_classes.py`). | Use the documented mapping consistently in label parsing, statistics, training, and evaluation. Original labels were modified in place; preserve originals in a separate directory for future transformations. |

## CityPersons Split Strategy (Finding 1 policy)

Verified directory layout (`data/raw/citypersons/images/`):
- `train`: 18 cities (aachen, bochum, bremen, cologne, darmstadt, dusseldorf, erfurt, hamburg, hanover, jena, krefeld, monchengladbach, strasbourg, stuttgart, tubingen, ulm, weimar, zurich)
- `val`: 3 cities (frankfurt, lindau, munster)
- `test`: 6 cities (berlin, bielefeld, bonn, leverkusen, mainz, munich)
- Train/val city overlap: none.

Documented split policy: use distinct city sets for training and validation; reserve the official CityPersons test split as the test set. The actual layout is consistent with a city-separated train/val/test split (no shared cities). Note: the actual training set contains 18 cities, not 15 as sometimes planned; documentation should reflect the actual layout rather than a planned 15-city subset.

## Raw Data Modification Note

UA-DETRAC label files were modified in place during class consolidation. The original class IDs were mapped to the final four-class scheme as follows:

- Original IDs `0` and `5` → `car`
- Original IDs `1` and `7` → `van`
- Original IDs `2` and `4` → `bus`
- Original IDs `3` and `6` → `others`

The final class configuration is:

```yaml
nc: 4
names:
  - car
  - van
  - bus
  - others
```

Because the original UA-DETRAC labels were modified in place, the original class annotations may not be recoverable from the processed files alone. Future dataset transformations should preferably preserve the original data and write modified annotations to a separate processed-data directory (e.g., `data/raw/ua_detrac_original/`).