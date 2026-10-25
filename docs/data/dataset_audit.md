# Raw Dataset Audit

## Summary

The raw UA-DETRAC and CityPersons datasets were audited for image-label matching, label validity, class distribution, potential train/test leakage, filename patterns, and image dimensions. The main findings were that CityPersons test images have no labels, UA-DETRAC has no separate validation split, and the two datasets use different image resolutions. The sampled visual similarity check did not reveal obvious train/test duplicates, and UA-DETRAC train/test sequences had no shared sequence IDs.

## Findings

| # | Issue | Evidence | Decision |
|---|---|---|---|
| 1 | CityPersons test has no labels | `audit_raw_citypersons.md`: 1,525 test images, 0 label files | Treat CityPersons test as unlabeled data. Use the labeled validation split for validation; do not assume the test split is an official validation set. |
| 2 | UA-DETRAC has no separate validation split | The dataset contains `train` and `test` folders only | Create a validation split from the training data later, grouping by source video ID to avoid placing frames from the same sequence in both train and validation. |
| 3 | UA-DETRAC car instance count mismatch | Training car count: 222,021; expected count: 222,028; difference: 7 instances | Unresolved. Original labels were unavailable for comparison, so the discrepancy was documented without further modification. |
| 4 | Potential train/test leakage in UA-DETRAC | Train: 32 unique sequence IDs; test: 13 unique sequence IDs; shared IDs: 0. Visual nearest-neighbor inspection of 8 test images from different sequences found no obvious duplicate or near-identical train images. | The sequence-level split appears separated. No obvious leakage was found in the sampled images, but this limited inspection does not prove that the entire dataset is free of duplicates. |
| 5 | UA-DETRAC filename pattern | Filenames follow the pattern `MVI_<sequence_id>_frame<frame_id>_...`. The training split contains 32 sequence IDs and the test split contains 13, with no overlap. | Extract the `MVI_<sequence_id>` prefix and use it as the grouping key when creating future splits. |
| 6 | Image dimensions | UA-DETRAC train: 34,374 images at 960 × 540; UA-DETRAC test: 15,292 images at 960 × 540; CityPersons train: 2,975 images at 2048 × 1024; CityPersons val: 502 images at 2048 × 1024. All checked images were readable, with zero errors. | Record these dimensions as the baseline for EDA and preprocessing. Revisit resizing and input resolution when configuring model training. |
| 7 | Empty labels in CityPersons | Train: 486 empty label files; val: 61 empty label files. No invalid label lines were reported. | Preserve these findings and inspect empty labels before deciding whether they represent legitimate images without target objects or annotation issues. |
| 8 | UA-DETRAC label class mapping | The final dataset uses four classes: `car`, `van`, `bus`, and `others`. The original class IDs were merged into four target classes. | Use the documented mapping consistently in label parsing, statistics, training, and evaluation. |

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

Because the original UA-DETRAC labels were modified in place, the original class annotations may not be recoverable from the processed files alone. Future dataset transformations should preferably preserve the original data and write modified annotations to a separate processed-data directory.