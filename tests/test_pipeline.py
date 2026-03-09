import json
import unittest
from unittest.mock import patch

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

    def test_api_client_uses_env_default_model_when_not_overridden(self):
        captured = {}

        class CapturingProvider:
            def __init__(self, api_key: str, model: str):
                captured["api_key"] = api_key
                captured["model"] = model

            def complete(self, *, system_prompt: str, user_message: str, max_tokens: int, context_tag: str) -> str:
                return "{}"

        fake_settings = type("FakeSettings", (), {"openai_model": "gpt-5-mini"})()
        with patch("lens.pipeline.api_client.get_settings", return_value=fake_settings), patch(
            "lens.pipeline.api_client.OpenAIChatProvider", CapturingProvider
        ):
            client = APIClient(api_key="test", system_prompt="system")

        self.assertEqual(client.model, "gpt-5-mini")
        self.assertEqual(captured["model"], "gpt-5-mini")

    def test_run_pipeline_passes_selected_model_to_api_client(self):
        captured = {}

        class CapturingClient:
            def __init__(self, *, api_key, system_prompt, retry_count, provider=None, model=None):
                captured["model"] = model
                self.call_count = 4

            def score_record(self, prompt: str, record_index: int):
                return {"sentiment_label": "positive", "confidence_score": 0.9, "reasoning": "Positive tone."}

            def extract_themes(self, prompt: str):
                return [
                    {
                        "label": "support quality",
                        "frequency": 1,
                        "dominant_sentiment": "positive",
                        "representative_quotes": ["Support was quick"],
                    }
                ]

            def generate_summary(self, prompt: str):
                return {
                    "executive_summary": "Support sentiment is strong overall. Teams describe response speed as the key reason trust is holding.",
                    "key_takeaways": ["Support quality was the strongest signal."],
                    "priority_actions": ["Keep the support playbook consistent."],
                    "issue_clusters": [
                        {
                            "label": "Support handoffs",
                            "severity": "low",
                            "frequency": 1,
                            "sentiment_direction": "positive",
                            "problem_patterns": ["Fast response times are driving confidence."],
                            "evidence_quotes": ["Support was quick"],
                            "recommended_actions": ["Preserve current staffing coverage."],
                            "trend_note": None,
                        }
                    ],
                    "positive_signals": [
                        {
                            "label": "Responsive support",
                            "frequency": 1,
                            "why_it_matters": "Fast responses are sustaining user confidence.",
                            "evidence_quotes": ["Support was quick"],
                            "recommended_preservation_actions": ["Protect rapid-response coverage."],
                        }
                    ],
                }

        batch = BatchInput(
            batch_label="Demo batch",
            domain_tag="cx",
            records=["Support was quick"],
            timestamps=None,
            context=ContextProfile(org_name="Meridian"),
            series_name=None,
            prior_cycle=None,
        )

        with patch("lens.pipeline.runner.APIClient", CapturingClient):
            result = run_pipeline(batch=batch, api_key="test", model="gpt-4o-mini")

        self.assertEqual(captured["model"], "gpt-4o-mini")
        self.assertEqual(result.record_count, 1)
        self.assertEqual(result.priority_actions, ["Keep the support playbook consistent."])
        self.assertEqual(result.positive_signals[0].label, "Responsive support")

    def test_run_pipeline_builds_analysis_result(self):
        provider = FakeProvider([
            json.dumps({"sentiment_label": "positive", "confidence_score": 0.9, "reasoning": "Customers praise fast support."}),
            json.dumps({"sentiment_label": "negative", "confidence_score": 0.8, "reasoning": "Customers report delayed support handoffs."}),
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
            json.dumps(
                {
                    "executive_summary": "Support quality is the core operational signal in this batch. Positive comments highlight fast responses, while negative comments point to slower handoffs that create friction.\n\nThe net picture is mixed, which means the team should protect the fast-response behavior while fixing the inconsistent escalation path.",
                    "priority_actions": [
                        "Audit slower support handoffs.",
                        "Preserve quick-response practices.",
                    ],
                    "issue_clusters": [
                        {
                            "label": "Support handoff delays",
                            "severity": "high",
                            "frequency": 1,
                            "sentiment_direction": "negative",
                            "problem_patterns": [
                                "Some users are waiting too long for ownership to transfer.",
                                "Resolution slows when tickets move between teams.",
                            ],
                            "evidence_quotes": ["Support was slow"],
                            "recommended_actions": ["Map the escalation path and remove transfer delays."],
                            "trend_note": "This issue is more visible than in the prior cycle.",
                        }
                    ],
                    "positive_signals": [
                        {
                            "label": "Fast first response",
                            "frequency": 1,
                            "why_it_matters": "Quick first contact is sustaining trust even when later stages slip.",
                            "evidence_quotes": ["Support was quick"],
                            "recommended_preservation_actions": ["Protect the current first-response staffing model."],
                        }
                    ],
                }
            ),
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
        self.assertTrue(result.executive_summary.startswith("Support quality"))
        self.assertEqual(result.issue_clusters[0].label, "Support handoff delays")
        self.assertEqual(result.positive_signals[0].label, "Fast first response")
        self.assertEqual(result.priority_actions[0], "Audit slower support handoffs.")


if __name__ == "__main__":
    unittest.main()
