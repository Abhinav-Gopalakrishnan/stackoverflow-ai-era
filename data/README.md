# Original collection and cleaned data

This is the team's original collection from the **Stack Exchange API v2.3**, site
`stackoverflow`, not a downloaded ready-made dataset. The study covers 1 January
2019 through 31 August 2026; the recorded collection snapshot is 3 October 2026.

## Included files

| Location | Contents |
|---|---|
| `original/<tag>/part-*.parquet` | All 309,179 collected question records across 13 tags, before deduplication/cleaning; raw owner IDs omitted, canonical source links added |
| `cleaned/questions_clean_v1.parquet.part-*.gz` | Complete compressed binary parts of the released 302,026-row, 39-column cleaned parquet |
| `cleaned/preview.csv` | Small readable preview of cleaned records with source links |
| `processed/weekly_counts.csv` | 5,600 observations: 14 series, 400 Tuesday-start weeks each |
| `processed/monthly_counts.csv` | Monthly API population counts |
| `processed/sampling_manifest.csv` | Selected sampling strata, inclusion weights and seeds |
| `processed/monthly_tag_tables.csv` | Cleaned weighted monthly summaries |
| `processed/features_{train,val,test}.parquet` | Existing feature tables for the original classifier |
| `submission_manifest.json` | Every public bundle file's row count where applicable, size and SHA-256 |

Every bundle file is below 50 MiB. A normal clone downloads these files without Git
LFS, API credentials, a private drive or a separate dataset attachment. The restored
316 MB parquet stays ignored; its small compressed parts are the committed source.

## Verify and restore

From the repository root with the project dependencies installed:

```bash
python scripts/submission_data.py --verify
python scripts/submission_data.py --restore
```

Restoration writes `data/processed/questions_clean_v1.parquet`, checks its byte count
and SHA-256, and refuses to overwrite a different existing file. Its SHA-256 is
`dd4a5d96df1cc93e1ccbad625bc51f01c65a96a32bce452469f1e62662dfaeaf`, matching the
original release and the final report. Parts are gzip-compressed **binary pieces**,
not independently readable parquet files; use the restoration command first.

```python
import pandas as pd

cleaned = pd.read_parquet("data/processed/questions_clean_v1.parquet")
original = pd.read_parquet("data/original/")
```

The original tag exports preserve collection order, duplicates, missing values,
HTML question bodies and sampling weights. Changes for the public export are
listed explicitly in the manifest. Direct owner IDs were removed; consequently,
rerunning owner-lookup enrichment from these public originals alone is not possible.
Use the included cleaned/enriched release for analysis, or perform a fresh API
collection with your own credentials using `notebooks/01_collection.ipynb`.

## Collection, validation and preprocessing evidence

- [Collection design and limitations](../docs/dataset_documentation.md),
  [sampling limitations](../docs/sampling_limitations.md),
  [field definitions](../docs/data_dictionary.md) and [collection configuration](../config.yaml).
- [API audit log](../logs/collection_log.csv) and the sampling manifest above.
- [Cleaning notebook](../notebooks/02_cleaning.ipynb): deduplication, UTC dates,
  prose/code separation, invalid-record removal, missing-age flags and target construction.
- [Final validation](../reports/review2/dataset/dataset_validation.json): unique IDs,
  complete required fields, positive weights, binary/consistent targets, date range
  and nonnegative account ages.

Original row totals include cross-tag duplicates; the cleaned table is unique by
question ID. The seven-day resolution label refers to **accepted-answer posting
time**, not the time of acceptance. Snapshot text can include later edits.
The sampled records are not a sitewide census. Weekly totals are collected separately.

## Attribution and privacy

Question text and code originate with the contributors credited on each linked
Stack Overflow question. Original exports include `source_url`; for cleaned records,
use `https://stackoverflow.com/q/<question_id>` to find the source and contributors.
Content retains the applicable license displayed by the source; see
[Stack Overflow's content licensing policy](https://stackoverflow.com/help/licensing).
The team added collection metadata, weights, cleaning, derived features and labels.

The export script omits raw owner/user IDs and profile attributes. The cleaned
release retains its existing pseudonymous `user_hash` for reproducible audits;
no hashing salt or API key is included. Local API caches and credentials remain
ignored. The public dashboard continues to use its smaller title-only/aggregate
bundle rather than loading full question text.

The PDF's appendix describes the earlier separate-dataset handoff. The bundle now
in this repository restores that exact same release; the checksum is unchanged.
