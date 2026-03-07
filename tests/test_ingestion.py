import unittest

from lens.ingestion.service import ValidationError, validate_batch


class IngestionTests(unittest.TestCase):
    def test_validate_csv_detects_text_and_timestamp_columns(self):
        csv_bytes = b"feedback,created_at\nGreat service,2026-03-01\n,2026-03-02\nNeeds work,2026-03-03\n"
        validated = validate_batch(csv_bytes=csv_bytes)

        self.assertEqual(validated.text_column, "feedback")
        self.assertEqual(validated.timestamp_column, "created_at")
        self.assertEqual(validated.records, ["Great service", "Needs work"])
        self.assertEqual(validated.timestamps, ["2026-03-01", "2026-03-03"])
        self.assertEqual(validated.rejected_row_count, 1)

    def test_validate_pasted_text_requires_non_empty_lines(self):
        validated = validate_batch(raw_text="Line one\n\nLine two\n")
        self.assertEqual(validated.records, ["Line one", "Line two"])
        self.assertEqual(validated.valid_record_count, 2)

    def test_validate_csv_rejects_missing_text_column(self):
        with self.assertRaises(ValidationError):
            validate_batch(csv_bytes=b"created_at\n2026-03-01\n")


if __name__ == "__main__":
    unittest.main()
