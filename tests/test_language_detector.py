import unittest

from lore_linker.services.language_detector import (
    detect_language,
    classify_language,
)


class TestLanguageDetector(unittest.TestCase):

    def test_detect_english(self):
        text = "Garen is a proud warrior of Demacia."
        self.assertEqual(detect_language(text), "en")

    def test_detect_japanese(self):
        text = "ガレンはデマーシアの誇り高き戦士です。"
        self.assertEqual(detect_language(text), "ja")

    def test_detect_empty_text(self):
        self.assertIsNone(detect_language(""))

    def test_classify_english_as_accepted(self):
        text = (
            "Garen is a proud warrior of Demacia. "
            "He protects the kingdom and fights for justice."
        )
        self.assertEqual(
            classify_language(text),
            ("accepted", None),
        )

    def test_classify_japanese_as_excluded(self):
        text = "ガレンはデマーシアの戦士です。彼は王国を守ります。"
        status, reason = classify_language(text)

        self.assertEqual(status, "excluded")
        self.assertIn("English probability is too low", reason)

    def test_classify_empty_text_as_excluded(self):
        self.assertEqual(
            classify_language(""),
            ("excluded", "Story body is empty."),
        )


if __name__ == "__main__":
    unittest.main()
