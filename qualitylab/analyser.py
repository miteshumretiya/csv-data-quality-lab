"""Pure-Python CSV profiling and safe export routines (no GUI imports)."""
from __future__ import annotations

import csv
import hashlib
import math
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


class AnalysisCancelled(Exception):
    """Raised when a user safely cancels long-running processing."""


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    non_empty: int
    missing: int
    numeric_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    kind: str


@dataclass(frozen=True)
class FileReport:
    source: str
    headers: tuple[str, ...]
    row_count: int
    duplicate_count: int
    missing_cells: int
    sample: tuple[tuple[str, ...], ...]
    columns: tuple[ColumnProfile, ...]
    quality_score: float
    bytes_on_disk: int


@dataclass
class _Accum:
    non_empty: int = 0
    missing: int = 0
    numeric_count: int = 0
    numeric_sum: float = 0.0
    numeric_min: float = math.inf
    numeric_max: float = -math.inf
    text_count: int = 0


def validate_csv_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        raise ValueError("The chosen CSV file does not exist.")
    if candidate.suffix.lower() != ".csv":
        raise ValueError("Please choose a .csv file.")
    return candidate


def _open_reader(path: Path):
    # Encoding errors are reported to the caller rather than silently replacing data.
    return open(path, "r", encoding="utf-8-sig", newline="")


def _check_headers(headers: list[str] | None) -> tuple[str, ...]:
    if not headers:
        raise ValueError("The CSV file has no header row.")
    cleaned = [h.strip() for h in headers]
    if any(not h for h in cleaned):
        raise ValueError("One or more column headings are blank.")
    if len({h.casefold() for h in cleaned}) != len(cleaned):
        raise ValueError("Column headings must be unique (ignoring case).")
    return tuple(cleaned)


def _valid_row(row: list[str], width: int, line_number: int) -> tuple[str, ...]:
    if len(row) != width:
        raise ValueError(f"Row near line {line_number} has {len(row)} fields, expected {width}.")
    return tuple(value.strip() for value in row)


def _digest(row: tuple[str, ...]) -> bytes:
    # A length prefix avoids ambiguity between joined cell values.
    data = b"".join(len(v.encode('utf-8')).to_bytes(8, 'big') + v.encode('utf-8') for v in row)
    return hashlib.blake2b(data, digest_size=16).digest()


def profile_csv(
    path: str | Path,
    preview_limit: int = 150,
    cancelled: Callable[[], bool] | None = None,
) -> FileReport:
    """Stream a CSV file and count missing cells, duplicate rows, and numeric columns.

    Only `preview_limit` rows are kept in the preview; de-duplication hashes
    are kept in memory, so very large files still require available RAM.
    """
    target = validate_csv_path(path)
    if preview_limit < 0:
        raise ValueError("Preview limit cannot be negative.")
    try:
        with _open_reader(target) as handle:
            reader = csv.reader(handle, strict=True)
            headers = _check_headers(next(reader, None))
            counters = [_Accum() for _ in headers]
            sample: list[tuple[str, ...]] = []
            fingerprints: set[bytes] = set()
            missing_cells = 0
            duplicate_count = 0
            row_count = 0
            for raw in reader:
                if cancelled and cancelled():
                    raise AnalysisCancelled("Analysis cancelled by the user.")
                if not raw or (len(raw) == 1 and not raw[0].strip()):
                    continue
                row = _valid_row(raw, len(headers), reader.line_num)
                row_count += 1
                if len(sample) < preview_limit:
                    sample.append(row)
                marker = _digest(row)
                if marker in fingerprints:
                    duplicate_count += 1
                else:
                    fingerprints.add(marker)
                for value, counter in zip(row, counters):
                    if value == "":
                        missing_cells += 1
                        counter.missing += 1
                        continue
                    counter.non_empty += 1
                    try:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError("Not a finite number")
                    except ValueError:
                        counter.text_count += 1
                    else:
                        counter.numeric_count += 1
                        counter.numeric_sum += number
                        counter.numeric_min = min(counter.numeric_min, number)
                        counter.numeric_max = max(counter.numeric_max, number)
    except (UnicodeError, csv.Error) as error:
        raise ValueError(f"Could not read CSV data: {error}") from error

    columns = []
    for name, counts in zip(headers, counters):
        purely_numeric = counts.numeric_count > 0 and counts.text_count == 0
        columns.append(ColumnProfile(
            name=name,
            non_empty=counts.non_empty,
            missing=counts.missing,
            numeric_count=counts.numeric_count,
            minimum=counts.numeric_min if purely_numeric else None,
            maximum=counts.numeric_max if purely_numeric else None,
            mean=counts.numeric_sum / counts.numeric_count if purely_numeric else None,
            kind="Numeric" if purely_numeric else "Text",
        ))
    total_cells = row_count * len(headers)
    penalty = missing_cells + duplicate_count * len(headers)
    score = 100.0 * max(0.0, 1.0 - penalty / total_cells) if total_cells else 0.0
    return FileReport(
        source=str(target.resolve()), headers=headers, row_count=row_count,
        duplicate_count=duplicate_count, missing_cells=missing_cells,
        sample=tuple(sample), columns=tuple(columns),
        quality_score=round(score, 1), bytes_on_disk=target.stat().st_size,
    )


def export_cleaned(source: str | Path, destination: str | Path, *, remove_duplicates: bool = True) -> int:
    """Safely write a separate trimmed CSV; never overwrite original data."""
    src = validate_csv_path(source).resolve()
    dest = Path(destination).resolve()
    if src == dest:
        raise ValueError("Please choose an output file different from the original CSV.")
    if dest.suffix.lower() != ".csv":
        raise ValueError("The output filename must end with .csv.")
    if not dest.parent.exists():
        raise ValueError("The output directory does not exist.")
    temporary: str | None = None
    count = 0
    try:
        with _open_reader(src) as input_handle:
            reader = csv.reader(input_handle, strict=True)
            headers = _check_headers(next(reader, None))
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=dest.parent,
                                             suffix=".csv", prefix=".csvlab_", delete=False) as output:
                temporary = output.name
                writer = csv.writer(output)
                writer.writerow(headers)
                seen: set[bytes] = set()
                for values in reader:
                    if not values or (len(values) == 1 and not values[0].strip()):
                        continue
                    row = _valid_row(values, len(headers), reader.line_num)
                    if remove_duplicates:
                        digest = _digest(row)
                        if digest in seen:
                            continue
                        seen.add(digest)
                    writer.writerow(row)
                    count += 1
        os.replace(temporary, dest)
        temporary = None
        return count
    except (UnicodeError, csv.Error) as error:
        raise ValueError(f"Could not clean CSV data: {error}") from error
    finally:
        if temporary and Path(temporary).exists():
            os.unlink(temporary)


def export_summary(report: FileReport, destination: str | Path) -> None:
    dest = Path(destination)
    if dest.suffix.lower() != ".csv":
        raise ValueError("Summary output must use the .csv extension.")
    with open(dest, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["dataset", "rows", "duplicates", "missing_cells", "quality_score", "column", "type", "non_empty", "missing", "mean"])
        for column in report.columns:
            writer.writerow([Path(report.source).name, report.row_count, report.duplicate_count,
                             report.missing_cells, report.quality_score, column.name, column.kind,
                             column.non_empty, column.missing, "" if column.mean is None else round(column.mean, 4)])
