from flask import Flask, render_template, request, jsonify

from lore_linker.services.database import initialize_database
from lore_linker.services.champion_data import get_registered_champions

from lore_linker.services.story_fetcher import (
    fetch_story_json,
    extract_story_title_from_json,
    extract_champion_biographies,
)

def create_app():
    app = Flask(__name__)

    initialize_database()

    @app.route("/")
    def story():
        champions = get_registered_champions()

        return render_template(
            "story.html",
            champions=champions,
        )

    @app.route("/api/stories/preview", methods=["POST"])
    def preview_story():
        data = request.get_json(silent=True) or {}
        story_url = data.get("url", "")

        if not isinstance(story_url, str) or not story_url.strip():
            return jsonify({
                "success": False,
                "error": "Please enter a Riot Universe URL.",
            }), 400

        try:
            story_data = fetch_story_json(story_url.strip())

            title = extract_story_title_from_json(story_data)
            biographies = extract_champion_biographies(story_data)

            if not title:
                return jsonify({
                    "success": False,
                    "error": "Story title could not be found.",
                }), 422

            if not biographies:
                return jsonify({
                    "success": False,
                    "error": "No featured champion biographies were found.",
                }), 422

            return jsonify({
                "success": True,
                "title": title,
                "biographies": biographies,
            })

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

        except RuntimeError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 502

    @app.route("/dictionary")
    def dictionary():
        return render_template("dictionary.html")

    @app.route("/network")
    def network():
        return render_template("network.html")

    return app