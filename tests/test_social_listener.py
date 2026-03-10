from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from growth_agent.social_listener.config_templates import ensure_default_configs
from growth_agent.social_listener.reply_handler import parse_selection


class SocialListenerTests(unittest.TestCase):
    def test_parse_selection_accepts_compact_commands(self) -> None:
        self.assertEqual(parse_selection("x1"), ("x", 1))
        self.assertEqual(parse_selection("B 12"), ("b", 12))

    def test_parse_selection_rejects_invalid_commands(self) -> None:
        with self.assertRaises(ValueError):
            parse_selection("tweet-1")

    def test_ensure_default_configs_creates_both_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            social_path, blog_path = ensure_default_configs(Path(tmpdir))
            self.assertTrue(social_path.exists())
            self.assertTrue(blog_path.exists())


if __name__ == "__main__":
    unittest.main()
