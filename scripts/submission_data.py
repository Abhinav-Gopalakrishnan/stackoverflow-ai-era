"""Build, verify and restore the public capstone data bundle.

The original exports omit owner_user_id. Cleaned parts reconstruct the exact
released parquet, including its original SHA-256, without Git LFS or API access.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/submission_manifest.json"
CHUNK_BYTES = 16 * 1024 * 1024
RAW_ROWS_PER_PART = 15_000
MAX_FILE_BYTES = 50 * 1024 * 1024


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def entry(path, **extra):
    size = path.stat().st_size
    if size >= MAX_FILE_BYTES:
        raise ValueError(f"Dataset file must be under 50 MiB: {path}")
    return {"path": str(path.relative_to(ROOT)), "bytes": size,
            "sha256": sha256(path), **extra}


def build():
    import pyarrow as pa
    import pyarrow.parquet as pq

    raw_paths = sorted((ROOT / "data/raw").glob("questions_*.parquet"))
    if len(raw_paths) != 13:
        raise ValueError("Expected the original 13 collected tag files")
    original_parts = []
    for source in raw_paths:
        table = pq.read_table(source)
        table = table.drop([c for c in ["owner_user_id", "user_id", "display_name",
                            "profile_image", "website_url"] if c in table.column_names])
        table = table.replace_schema_metadata(None)
        table = table.append_column("source_url", pa.array(
            [f"https://stackoverflow.com/q/{qid}" for qid in table["question_id"].to_pylist()]))
        tag = source.stem.removeprefix("questions_")
        directory = ROOT / "data/original" / tag
        directory.mkdir(parents=True, exist_ok=True)
        for index, start in enumerate(range(0, table.num_rows, RAW_ROWS_PER_PART)):
            part = table.slice(start, RAW_ROWS_PER_PART)
            destination = directory / f"part-{index:03d}.parquet"
            pq.write_table(part, destination, compression="zstd", compression_level=6)
            original_parts.append(entry(destination, rows=part.num_rows, tag=tag))
        print(f"Original {tag}: {table.num_rows:,} rows", flush=True)

    source = ROOT / "data/processed/questions_clean_v1.parquet"
    parquet = pq.ParquetFile(source)
    directory = ROOT / "data/cleaned"
    directory.mkdir(parents=True, exist_ok=True)
    cleaned_parts = []
    with source.open("rb") as stream:
        index = 0
        while block := stream.read(CHUNK_BYTES):
            destination = directory / f"questions_clean_v1.parquet.part-{index:03d}.gz"
            with destination.open("wb") as output:
                with gzip.GzipFile(filename="", mode="wb", fileobj=output,
                                   compresslevel=6, mtime=0) as compressed:
                    compressed.write(block)
            cleaned_parts.append(entry(destination, uncompressed_bytes=len(block)))
            index += 1
    preview = ROOT / "reports/review2/dataset/final_dataset_sample.csv"
    shutil.copyfile(preview, directory / "preview.csv")
    manifest = {
        "format_version": 1,
        "source": "Original team collection from Stack Exchange API v2.3, site=stackoverflow",
        "study_start": "2019-01-01", "study_end": "2026-08-31",
        "collection_date": "2026-10-03",
        "original": {"rows": sum(p["rows"] for p in original_parts),
                     "files": original_parts,
                     "transformations": ["Omit raw owner/user/profile identifiers",
                                         "Add canonical source_url for attribution",
                                         "Re-encode as Zstandard parquet; preserve collected values and row order within each tag"]},
        "cleaned": {"rows": parquet.metadata.num_rows,
                    "columns": len(parquet.schema_arrow.names),
                    "bytes": source.stat().st_size, "sha256": sha256(source),
                    "restore_path": "data/processed/questions_clean_v1.parquet",
                    "encoding": "Independently gzip-compressed consecutive binary parts, in manifest order",
                    "files": cleaned_parts},
        "notes": ["Original tag files contain cross-tag duplicates; cleaned IDs are unique.",
                  "No API key, salt, direct owner ID or user profile is included in this bundle.",
                  "The cleaned release retains pseudonymous user_hash, not raw user IDs.",
                  "Source text and code retain the license and authorship of the linked Stack Overflow posts.",
                  "Historical snapshot text may contain edits after posting; targets use answer posting time, not the acceptance event."],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Published {len(original_parts)} original shards and {len(cleaned_parts)} cleaned parts", flush=True)


def verify():
    import pyarrow.parquet as pq

    manifest = json.loads(MANIFEST.read_text())
    original_rows = 0
    for group in ["original", "cleaned"]:
        for part in manifest[group]["files"]:
            path = ROOT / part["path"]
            if path.stat().st_size != part["bytes"] or sha256(path) != part["sha256"]:
                raise ValueError(f"Size/hash mismatch: {path}")
            if path.stat().st_size >= MAX_FILE_BYTES:
                raise ValueError(f"Oversize file: {path}")
            if group == "original":
                parquet = pq.ParquetFile(path)
                if parquet.metadata.num_rows != part["rows"]:
                    raise ValueError(f"Row count mismatch: {path}")
                forbidden = {"owner_user_id", "user_id", "display_name", "profile_image", "website_url"}
                if forbidden.intersection(parquet.schema_arrow.names):
                    raise ValueError(f"Direct user identifier in {path}")
                original_rows += part["rows"]
    digest = hashlib.sha256()
    byte_count = 0
    for part in manifest["cleaned"]["files"]:
        with gzip.open(ROOT / part["path"], "rb") as stream:
            part_count = 0
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                part_count += len(block)
            if part_count != part["uncompressed_bytes"]:
                raise ValueError(f"Uncompressed size mismatch: {part['path']}")
            byte_count += part_count
    if (original_rows != manifest["original"]["rows"] or
            byte_count != manifest["cleaned"]["bytes"] or
            digest.hexdigest() != manifest["cleaned"]["sha256"]):
        raise ValueError("Dataset totals or reconstructed checksum do not match")
    print(f"Verified {original_rows:,} original rows; exact cleaned parquet "
          f"({manifest['cleaned']['rows']:,} rows, {byte_count:,} bytes)")
    return manifest


def restore(destination=None):
    manifest = verify()
    destination = Path(destination) if destination else ROOT / manifest["cleaned"]["restore_path"]
    if destination.exists():
        if sha256(destination) == manifest["cleaned"]["sha256"]:
            print(f"Already restored and checksum matches: {destination}")
            return
        raise FileExistsError(f"Refusing to replace a different existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".restore-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            for part in manifest["cleaned"]["files"]:
                with gzip.open(ROOT / part["path"], "rb") as stream:
                    shutil.copyfileobj(stream, output)
        if sha256(temporary) != manifest["cleaned"]["sha256"]:
            raise ValueError("Restored file checksum mismatch")
        os.replace(temporary, destination)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()
    print(f"Restored: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", action="store_true")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--restore", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional restored parquet destination")
    args = parser.parse_args()
    if args.build:
        build()
        verify()
    elif args.restore:
        restore(args.output)
    else:
        verify()
