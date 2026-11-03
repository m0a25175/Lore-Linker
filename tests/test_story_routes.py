import unittest
from unittest.mock import patch

from lore_linker import create_app


class TestStoryRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch("lore_linker.fetch_story_json")
    @patch("lore_linker.extract_story_title_from_json")
    @patch("lore_linker.extract_champion_biographies")
    def test_preview_story_success(
        self,
        mock_biographies,
        mock_title,
        mock_fetch,
    ):
        mock_fetch.return_value = {"story": {}}
        mock_title.return_value = "The Soldier and the Hag"
        mock_biographies.return_value = [
            {
                "champion_name": "Garen",
                "body": "Garen biography text.",
            }
        ]

        response = self.client.post(
            "/api/stories/preview",
            json={
                "url": (
                    "https://universe.leagueoflegends.com/"
                    "en_US/story/champion/garen-color-story/"
                )
            },
        )

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertTrue(result["success"])
        self.assertEqual(
            result["title"],
            "The Soldier and the Hag",
        )
        self.assertEqual(
            result["biographies"][0]["champion_name"],
            "Garen",
        )

    def test_preview_story_missing_url(self):
        response = self.client.post(
            "/api/stories/preview",
            json={},
        )

        self.assertEqual(response.status_code, 400)

        result = response.get_json()

        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()