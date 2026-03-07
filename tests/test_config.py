import os
import unittest
from unittest.mock import patch

from lens import config


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        config.get_settings.cache_clear()

    def test_openai_model_defaults_to_gpt_5_mini(self):
        with patch.dict(os.environ, {}, clear=True):
            config.get_settings.cache_clear()
            settings = config.get_settings()

        self.assertEqual(settings.openai_model, "gpt-5-mini")
        self.assertIn("gpt-5-mini", settings.allowed_models)
        self.assertFalse(settings.admin_auth_enabled)

    def test_custom_model_and_admin_password_are_loaded(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_MODEL": "gpt-4o-mini",
                "LENS_ADMIN_PASSWORD": "secret",
                "OPENAI_API_KEY": "sk-test",
            },
            clear=True,
        ):
            config.get_settings.cache_clear()
            settings = config.get_settings()

        self.assertEqual(settings.openai_model, "gpt-4o-mini")
        self.assertTrue(settings.admin_auth_enabled)
        self.assertTrue(settings.live_runs_locked)
        self.assertEqual(settings.allowed_models[0], "gpt-4o-mini")


if __name__ == "__main__":
    unittest.main()
