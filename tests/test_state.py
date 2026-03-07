from types import SimpleNamespace
import unittest

from lens.config import Settings
from lens.ui import state


class FakeSessionState(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as error:
            raise AttributeError(item) from error

    def __setattr__(self, key, value):
        self[key] = value


class SessionStateTests(unittest.TestCase):
    def test_init_session_state_sets_model_and_resets_stuck_pipeline(self):
        fake_streamlit = SimpleNamespace(
            session_state=FakeSessionState(
                {
                    "pipeline_running": True,
                    "current_result": object(),
                    "selected_model": None,
                }
            )
        )
        original_streamlit = state.st
        state.st = fake_streamlit
        try:
            settings = Settings(
                database_url=None,
                openai_api_key="sk-test",
                created_by="tester",
                openai_model="gpt-5-mini",
                admin_run_password="secret",
                allowed_models=("gpt-5-mini", "gpt-4o-mini", "gpt-5"),
            )
            state.init_session_state(settings)
        finally:
            state.st = original_streamlit

        self.assertEqual(fake_streamlit.session_state["app_mode"], "live")
        self.assertEqual(fake_streamlit.session_state["selected_model"], "gpt-5-mini")
        self.assertFalse(fake_streamlit.session_state["pipeline_running"])

    def test_init_session_state_clears_admin_unlock_when_auth_disabled(self):
        fake_streamlit = SimpleNamespace(
            session_state=FakeSessionState(
                {
                    "admin_unlocked": True,
                    "selected_model": "invalid-model",
                }
            )
        )
        original_streamlit = state.st
        state.st = fake_streamlit
        try:
            settings = Settings(
                database_url=None,
                openai_api_key="sk-test",
                created_by="tester",
                openai_model="gpt-5-mini",
                admin_run_password=None,
                allowed_models=("gpt-5-mini", "gpt-4o-mini", "gpt-5"),
            )
            state.init_session_state(settings)
        finally:
            state.st = original_streamlit

        self.assertFalse(fake_streamlit.session_state["admin_unlocked"])
        self.assertEqual(fake_streamlit.session_state["selected_model"], "gpt-5-mini")


if __name__ == "__main__":
    unittest.main()
