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

    @patch("lore_linker.register_story")
    def test_create_story_success(self, mock_register):
        mock_register.return_value = {
            "success": True,
            "duplicate": False,
            "story_id": 1,
            "champion_id": "Garen",
            "title": "The Soldier and the Hag",
            "language_status": "accepted",
            "language_reason": None,
        }

        response = self.client.post(
            "/api/stories",
            json={
                "champion_name": "Garen",
                "title": "The Soldier and the Hag",
                "body": "Garen biography text.",
                "source_url": "https://universe.leagueoflegends.com/example/",
                "registration_method": "url",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])

    @patch("lore_linker.register_story")
    def test_create_story_duplicate_conflict(self, mock_register):
        mock_register.return_value = {
            "success": False,
            "duplicate": True,
            "error": "Duplicate story found.",
        }

        response = self.client.post(
            "/api/stories",
            json={
                "champion_name": "Garen",
                "title": "Duplicate Story",
                "body": "Garen biography text.",
                "source_url": "https://universe.leagueoflegends.com/example/",
                "registration_method": "url",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.get_json()["duplicate"])

    @patch("lore_linker.register_story")
    def test_create_story_validation_error(self, mock_register):
        mock_register.side_effect = ValueError("Invalid story data.")

        response = self.client.post(
            "/api/stories",
            json={
                "champion_name": "Garen",
                "title": "",
                "body": "",
                "registration_method": "manual",
            },
        )

        self.assertEqual(response.status_code, 400)

        result = response.get_json()

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid story data.")
    @patch("lore_linker.get_stories")
    def test_list_stories_success(self, mock_get_stories):
        mock_get_stories.return_value = [
            {
                "id": 1,
                "champion_id": "Garen",
                "title": "The Soldier and the Hag",
                "body": "Garen biography text.",
            }
        ]

        response = self.client.get("/api/stories")

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertTrue(result["success"])
        self.assertEqual(len(result["stories"]), 1)
        self.assertEqual(
            result["stories"][0]["champion_id"],
            "Garen",
        )

    @patch("lore_linker.get_stories")
    def test_list_stories_by_champion(self, mock_get_stories):
        mock_get_stories.return_value = []

        response = self.client.get(
            "/api/stories?champion=Garen"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

        mock_get_stories.assert_called_once_with("Garen")

    @patch("lore_linker.get_story_by_id")
    def test_retrieve_story_success(self, mock_get_story):
        mock_get_story.return_value = {
            "id": 1,
            "champion_id": "Garen",
            "title": "The Soldier and the Hag",
            "body": "Garen biography text.",
        }

        response = self.client.get("/api/stories/1")

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertTrue(result["success"])
        self.assertEqual(result["story"]["id"], 1)

    @patch("lore_linker.get_story_by_id")
    def test_retrieve_story_not_found(self, mock_get_story):
        mock_get_story.return_value = None

        response = self.client.get("/api/stories/99999")

        self.assertEqual(response.status_code, 404)

        result = response.get_json()

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Story not found.")

    @patch("lore_linker.update_story")
    def test_edit_story_success(self, mock_update):
        mock_update.return_value = {
            "success": True,
            "duplicate": False,
            "story_id": 1,
            "champion_id": "Garen",
            "title": "Updated Story",
            "language_status": "accepted",
        }

        response = self.client.put(
            "/api/stories/1",
            json={
                "champion_name": "Garen",
                "title": "Updated Story",
                "body": "Updated Garen biography text.",
                "source_url": "https://universe.leagueoflegends.com/example/",
                "registration_method": "url",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    @patch("lore_linker.update_story")
    def test_edit_story_duplicate_conflict(self, mock_update):
        mock_update.return_value = {
            "success": False,
            "duplicate": True,
            "error": "Duplicate story found.",
        }

        response = self.client.put(
            "/api/stories/1",
            json={
                "champion_name": "Garen",
                "title": "Duplicate Story",
                "body": "Duplicate biography text.",
                "source_url": "https://universe.leagueoflegends.com/example/",
                "registration_method": "url",
            },
        )

        self.assertEqual(response.status_code, 409)

    @patch("lore_linker.update_story")
    def test_edit_story_not_found(self, mock_update):
        mock_update.return_value = {
            "success": False,
            "duplicate": False,
            "error": "Story not found.",
        }

        response = self.client.put(
            "/api/stories/99999",
            json={
                "champion_name": "Garen",
                "title": "Updated Story",
                "body": "Updated biography text.",
                "registration_method": "manual",
            },
        )

        self.assertEqual(response.status_code, 404)

    @patch("lore_linker.delete_story")
    def test_remove_story_success(self, mock_delete):
        mock_delete.return_value = True

        response = self.client.delete("/api/stories/1")

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "Story deleted successfully.",
        )

    @patch("lore_linker.delete_story")
    def test_remove_story_not_found(self, mock_delete):
        mock_delete.return_value = False

        response = self.client.delete("/api/stories/99999")

        self.assertEqual(response.status_code, 404)

        result = response.get_json()

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Story not found.")

if __name__ == "__main__":
    unittest.main()