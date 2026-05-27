"""CSV metadata helpers."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from .constants import BIBLIOGRAPHY_FIELDS, READING_STATUS_FIELDS


def _read_rows(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            normalized = {field: row.get(field, "") for field in fields}
            for key, value in row.items():
                if key not in normalized and key is not None:
                    normalized[key] = value or ""
            rows.append(normalized)
        return rows


def _write_rows(path: Path, fields: Iterable[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(dict.fromkeys(fields))
    for row in rows:
        for key in row:
            if key not in field_list:
                field_list.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list)
        writer.writeheader()
        writer.writerows(rows)


def ensure_metadata_files(metadata_dir: Path) -> None:
    metadata_dir.mkdir(parents=True, exist_ok=True)
    reading_status = metadata_dir / "reading_status.csv"
    bibliography = metadata_dir / "bibliography.csv"
    if not reading_status.exists():
        _write_rows(reading_status, READING_STATUS_FIELDS, [])
    if not bibliography.exists():
        _write_rows(bibliography, BIBLIOGRAPHY_FIELDS, [])


def read_status(path: Path) -> list[dict[str, str]]:
    return _read_rows(path, READING_STATUS_FIELDS)


def write_status(path: Path, rows: list[dict[str, str]]) -> None:
    _write_rows(path, READING_STATUS_FIELDS, rows)


def upsert_status(path: Path, file_name: str, updates: dict[str, str | bool]) -> None:
    rows = read_status(path)
    row = next((candidate for candidate in rows if candidate.get("file_name") == file_name), None)
    if row is None:
        row = {field: "" for field in READING_STATUS_FIELDS}
        row["file_name"] = file_name
        row["human_verified"] = "false"
        row["revision_needed"] = "false"
        rows.append(row)

    for key, value in updates.items():
        if key == "human_verified" and value is True:
            raise ValueError(
                "human_verified must only be set by explicit human verification command"
            )
        row[key] = _bool_to_str(value)

    write_status(path, rows)


def mark_human_verified(path: Path, file_name: str) -> None:
    rows = read_status(path)
    row = next((candidate for candidate in rows if candidate.get("file_name") == file_name), None)
    if row is None:
        raise ValueError(f"No reading_status row found for {file_name}")
    row["human_verified"] = "true"
    write_status(path, rows)


def _bool_to_str(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value
