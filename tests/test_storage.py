import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from lens.pipeline.models import AnalysisResult, ContextProfile, RecordResult, ThemeResult
from lens.storage.models import StoredAnalysis
from lens.storage.service import bootstrap_database, save_analysis


class FakeCursor:
    def __init__(self, fetch_results=None):
        self.fetch_results = list(fetch_results or [])
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((str(query), params))

    def fetchone(self):
        return self.fetch_results.pop(0)

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class StorageTests(unittest.TestCase):
    def test_bootstrap_skips_seed_when_series_exist(self):
        from lens import config
        from lens.storage import service

        tmp_dir = Path("tests_runtime")
        tmp_dir.mkdir(exist_ok=True)
        schema_path = tmp_dir / "schema.sql"
        seed_path = tmp_dir / "seed.sql"
        schema_path.write_text("SELECT 1;", encoding="utf-8")
        seed_path.write_text("SELECT 2;", encoding="utf-8")

        class TestSettings(config.Settings):
            @property
            def schema_path(self):
                return schema_path

            @property
            def seed_path(self):
                return seed_path

        fake_settings = TestSettings(
            database_url="postgres://demo",
            openai_api_key=None,
            created_by="tester",
        )

        cursor = FakeCursor(fetch_results=[{"total": 1}])
        connection = FakeConnection(cursor)

        @contextmanager
        def fake_get_connection():
            yield connection

        original_get_settings = service.get_settings
        original_get_connection = service.get_connection
        service.get_settings = lambda: fake_settings
        service.get_connection = fake_get_connection
        try:
            ok, message = bootstrap_database()
        finally:
            service.get_settings = original_get_settings
            service.get_connection = original_get_connection
            schema_path.unlink(missing_ok=True)
            seed_path.unlink(missing_ok=True)
            tmp_dir.rmdir()

        self.assertTrue(ok)
        self.assertIn("initialized", message.lower())
        self.assertEqual(len(cursor.executed), 2)

    def test_save_analysis_assigns_run_sequence(self):
        from lens.storage import service

        cursor = FakeCursor(fetch_results=[{"next_run_sequence": 3}])
        connection = FakeConnection(cursor)

        @contextmanager
        def fake_get_connection():
            yield connection

        original_get_connection = service.get_connection
        original_execute_values = service.execute_values
        original_load_analysis = service.load_analysis
        service.get_connection = fake_get_connection
        service.execute_values = lambda *args, **kwargs: None
        service.load_analysis = lambda analysis_id: StoredAnalysis(
            analysis_id=analysis_id,
            batch_label="Demo",
            domain_tag="cx",
            series_name="Series",
            run_sequence=3,
            created_at=datetime.now(timezone.utc),
            record_count=1,
            sentiment_split={"positive": 100.0, "neutral": 0.0, "negative": 0.0},
            themes=[],
            executive_summary="summary",
            anomaly_flags=[],
            anomaly_count=0,
            context_profile=None,
            records=[],
            prior_cycle_context=None,
        )
        try:
            result = AnalysisResult(
                analysis_id="analysis-1",
                batch_label="Demo",
                domain_tag="cx",
                series_name="Series",
                run_sequence=None,
                records=[
                    RecordResult(
                        record_id="record-1",
                        sequence_number=1,
                        text_body="Great service",
                        sentiment_label="positive",
                        confidence_score=0.9,
                        reasoning="Positive tone.",
                    )
                ],
                themes=[ThemeResult(label="service", frequency=1, dominant_sentiment="positive", representative_quotes=["Great service"])],
                executive_summary="summary",
                anomaly_flags=[],
                sentiment_split={"positive": 100.0, "neutral": 0.0, "negative": 0.0},
                anomaly_count=0,
                context_profile=ContextProfile(org_name="Org"),
                prior_cycle_ref=None,
                prior_cycle_context=None,
                record_count=1,
                records_scored=1,
                records_failed=0,
                api_call_count=3,
                duration_seconds=1.0,
            )
            stored = save_analysis(result)
        finally:
            service.get_connection = original_get_connection
            service.execute_values = original_execute_values
            service.load_analysis = original_load_analysis

        self.assertEqual(result.run_sequence, 3)
        self.assertEqual(stored.run_sequence, 3)
        self.assertTrue(connection.committed)


if __name__ == "__main__":
    unittest.main()
