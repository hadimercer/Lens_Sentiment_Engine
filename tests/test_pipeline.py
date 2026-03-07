import json
import unittest

from lens.pipeline.api_client import APIClient, LLMProvider
from lens.pipeline.models import BatchInput, ContextProfile, PriorCycleContext
from lens.pipeline.runner import run_pipeline


class FakeProvider(LLMProvider):
    def __init__(self, responses):
        self.responses = list(responses)

    def complete(self, *, system_prompt: str, user_message: str, max_tokens: int, context_tag: str) -> str:
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class PipelineTests(unittest.TestCase):
    def test_api_client_retries_after_malformed_json(self):
        provider = FakeProvider([
            "not-json",
            json.dumps({"sentiment_label": "positive", "confidence_score": 0.8, "reasoning": "Clear praise."}),
        ])
        client = APIClient(api_key="test", system_prompt="system", provider=provider)

        result = client.score_record("prompt", record_index=0)

        self.assertIsNotNone(result)
        self.assertEqual(result["sentiment_label"], "positive")
        self.assertEqual(client.call_count, 2)

    def test_run_pipeline_builds_analysis_result(self):
        provider = FakeProvider([
            json.dumps({"sentiment_label": "positive", "confidence_score": 0.9, "reasoning": "Positive tone."}),
            json.dumps({"sentiment_label": "negative", "confidence_score": 0.8, "reasoning": "Negative tone."}),
            json.dumps(
                {
                    "themes": [
                        {
                            "label": "support quality",
                            "frequency": 2,
                            "dominant_sentiment": "neutral",
                            "representative_quotes": ["Support was quick", "Support was slow"],
                        }
                    ]
                }
            ),
            json.dumps({"executive_summary": "Mixed sentiment with support as the main theme."}),
        ])
        batch = BatchInput(
            batch_label="Demo batch",
            domain_tag="cx",
            records=["Support was quick", "Support was slow"],
            timestamps=None,
            context=ContextProfile(org_name="Meridian"),
            series_name="NPS Q-Series",
            prior_cycle=PriorCycleContext(
                analysis_id="prior-id",
                batch_label="Previous batch",
                run_sequence=1,
                sentiment_split={"positive": 50, "neutral": 25, "negative": 25},
                top_themes=["billing"],
                executive_summary="Earlier run summary.",
            ),
        )

        result = run_pipeline(batch=batch, api_key="test", provider=provider)

        self.assertEqual(result.record_count, 2)
        self.assertEqual(result.prior_cycle_ref, "prior-id")
        self.assertEqual(result.themes[0].label, "support quality")
        self.assertTrue(result.executive_summary.startswith("Mixed sentiment"))


if __name__ == "__main__":
    unittest.main()
