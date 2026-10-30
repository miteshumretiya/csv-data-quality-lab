"""Automated checks for CSV analysis logic; run with unittest discovery."""
from __future__ import annotations
import csv
import tempfile
import unittest
from pathlib import Path
from qualitylab.analyser import (AnalysisCancelled, export_cleaned, export_summary,
                                  profile_csv, validate_csv_path)


class CsvQualityTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.source = self.make("sales.csv", "ID,Region,Units,Cost\n1,North,2,10\n2,South,,20\n2,South,,20\n3,East,4,30\n")

    def make(self, name, contents):
        path = self.base / name
        path.write_text(contents, encoding="utf-8")
        return path

    def test_file_path_is_valid(self):
        self.assertEqual(validate_csv_path(self.source), self.source)

    def test_missing_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            validate_csv_path(self.base / "absent.csv")

    def test_wrong_extension_rejected(self):
        path = self.make("data.txt", "A\n1\n")
        with self.assertRaisesRegex(ValueError, "csv"):
            validate_csv_path(path)

    def test_counts_rows(self):
        self.assertEqual(profile_csv(self.source).row_count, 4)

    def test_detects_duplicates(self):
        self.assertEqual(profile_csv(self.source).duplicate_count, 1)

    def test_detects_missing_cells(self):
        self.assertEqual(profile_csv(self.source).missing_cells, 2)

    def test_quality_score(self):
        # Four rows x four fields; penalty=2 empty cells + 4 duplicate-row cells.
        self.assertEqual(profile_csv(self.source).quality_score, 62.5)

    def test_profile_names(self):
        self.assertEqual(profile_csv(self.source).headers, ("ID", "Region", "Units", "Cost"))

    def test_numeric_field(self):
        self.assertEqual(profile_csv(self.source).columns[2].kind, "Numeric")

    def test_numeric_mean_ignores_blanks(self):
        self.assertAlmostEqual(profile_csv(self.source).columns[2].mean, 3.0)

    def test_text_column(self):
        self.assertEqual(profile_csv(self.source).columns[1].kind, "Text")

    def test_preview_limit(self):
        self.assertEqual(len(profile_csv(self.source, preview_limit=2).sample), 2)

    def test_zero_preview(self):
        self.assertEqual(len(profile_csv(self.source, preview_limit=0).sample), 0)

    def test_negative_preview_rejected(self):
        with self.assertRaises(ValueError):
            profile_csv(self.source, preview_limit=-1)

    def test_empty_csv_rejected(self):
        with self.assertRaisesRegex(ValueError, "header"):
            profile_csv(self.make("empty.csv", ""))

    def test_duplicate_column_names_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            profile_csv(self.make("duplicate.csv", "name,Name\na,b\n"))

    def test_blank_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "blank"):
            profile_csv(self.make("blank.csv", "ID,,Price\n1,A,1\n"))

    def test_bad_row_width_rejected(self):
        with self.assertRaisesRegex(ValueError, "fields"):
            profile_csv(self.make("width.csv", "A,B\n1,2,3\n"))

    def test_utf8_bom_supported(self):
        p = self.base / "bom.csv"
        p.write_bytes(b"\xef\xbb\xbfName,Qty\nTea,2\n")
        self.assertEqual(profile_csv(p).headers[0], "Name")

    def test_utf8_invalid_bytes_reported(self):
        p = self.base / "broken.csv"
        p.write_bytes(b"Key\n\xff\xfe\n")
        with self.assertRaises(ValueError):
            profile_csv(p)

    def test_cancelled_job(self):
        with self.assertRaises(AnalysisCancelled):
            profile_csv(self.source, cancelled=lambda: True)

    def test_blank_data_lines_skipped(self):
        p = self.make("blanks.csv", "A,B\n\n1,2\n\n")
        self.assertEqual(profile_csv(p).row_count, 1)

    def test_spaces_trimmed_for_duplicates(self):
        p = self.make("space.csv", "A,B\n hi ,1\nhi,1\n")
        self.assertEqual(profile_csv(p).duplicate_count, 1)

    def test_non_finite_values_are_not_numeric(self):
        p = self.make("infinite.csv", "Value\nInfinity\n1\n")
        self.assertEqual(profile_csv(p).columns[0].kind, "Text")

    def test_empty_dataset_has_zero_score(self):
        p = self.make("headersonly.csv", "A,B\n")
        self.assertEqual(profile_csv(p).quality_score, 0.0)

    def test_export_cleaned_removes_duplicates(self):
        dest = self.base / "clean.csv"
        self.assertEqual(export_cleaned(self.source, dest), 3)
        self.assertEqual(profile_csv(dest).duplicate_count, 0)

    def test_export_cleaned_preserves_source(self):
        before = self.source.read_bytes()
        export_cleaned(self.source, self.base / "output.csv")
        self.assertEqual(self.source.read_bytes(), before)

    def test_export_cleaned_without_dedup(self):
        dest = self.base / "all.csv"
        self.assertEqual(export_cleaned(self.source, dest, remove_duplicates=False), 4)

    def test_cannot_export_over_source(self):
        with self.assertRaisesRegex(ValueError, "different"):
            export_cleaned(self.source, self.source)

    def test_export_name_extension_check(self):
        with self.assertRaisesRegex(ValueError, "csv"):
            export_cleaned(self.source, self.base / "out.txt")

    def test_summary_export(self):
        report = profile_csv(self.source)
        target = self.base / "summary.csv"
        export_summary(report, target)
        with target.open(newline='', encoding='utf-8') as stream:
            records = list(csv.reader(stream))
        self.assertEqual(len(records), len(report.headers) + 1)
        self.assertEqual(records[1][5], 'ID')

    def test_summary_extension_check(self):
        with self.assertRaises(ValueError):
            export_summary(profile_csv(self.source), self.base / "summary.txt")


if __name__ == "__main__":
    unittest.main()
