import unittest

from lore_linker.services.story_fetcher import (
    validate_story_url,
    extract_champion_biographies,
    extract_story_title_from_json,
)


class TestStoryFetcher(unittest.TestCase):

    def test_validate_story_url(self):
        valid_url = (
            "https://universe.leagueoflegends.com/"
            "en_US/story/champion/garen-color-story/"
        )

        invalid_urls = [
            "http://universe.leagueoflegends.com/en_US/story/",
            "https://example.com/en_US/story/",
            "https://universe.leagueoflegends.com.evil.com/en_US/story/",
            "https://universe.leagueoflegends.com.evil.com/",
        ]

        self.assertTrue(validate_story_url(valid_url))

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(validate_story_url(url))

    def test_extract_story_title(self):
        data = {
            "story": {
                "title": "  The Soldier and the Hag  "
            }
        }

        self.assertEqual(
            extract_story_title_from_json(data),
            "The Soldier and the Hag",
        )

    def test_extract_champion_biographies(self):
        data = {
            "story": {
                "story-sections": [
                    {
                        "featured-champions": [
                            {
                                "name": "Garen",
                                "biography": {
                                    "full": "<p>Garen profile.</p>"
                                },
                            },
                            {
                                "name": None,
                                "biography": {
                                    "full": "<p>Unknown.</p>"
                                },
                            },
                            {
                                "name": "Lux",
                                "biography": {
                                    "full": ""
                                },
                            },
                            {
                                "name": "Darius",
                                "biography": {
                                    "full": "<div>No paragraph.</div>"
                                },
                            },
                        ]
                    }
                ]
            }
        }

        result = extract_champion_biographies(data)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["champion_name"], "Garen")
        self.assertEqual(result[0]["body"], "Garen profile.")


if __name__ == "__main__":
    unittest.main()