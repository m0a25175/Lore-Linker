from flask import Flask, render_template, request, jsonify

from lore_linker.services.database import initialize_database
from lore_linker.services.champion_data import get_registered_champions

from lore_linker.services.story_fetcher import (
    fetch_story_json,
    extract_story_title_from_json,
    extract_champion_biographies,
)

from lore_linker.services.story_manager import (
    register_story,
    get_stories,
    get_story_by_id,
    update_story,
    delete_story,
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

    @app.route("/api/stories", methods=["POST"])
    def create_story():
        data = request.get_json(silent=True) or {}

        try:
            result = register_story(
                champion_name=data.get("champion_name"),
                title=data.get("title"),
                body=data.get("body"),
                source_url=data.get("source_url"),
                registration_method=data.get(
                    "registration_method",
                    "url",
                ),
                allow_duplicate=data.get(
                    "allow_duplicate",
                    False,
                ),
            )

            if result["duplicate"] and not result["success"]:
                return jsonify(result), 409

            return jsonify(result), 201

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/api/stories", methods=["GET"])
    def list_stories():
        champion_name = request.args.get("champion")

        try:
            stories = get_stories(champion_name)

            return jsonify({
                "success": True,
                "stories": stories,
            })

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/api/stories/<int:story_id>", methods=["GET"])
    def retrieve_story(story_id):
        story = get_story_by_id(story_id)

        if story is None:
            return jsonify({
                "success": False,
                "error": "Story not found.",
            }), 404

        return jsonify({
            "success": True,
            "story": story,
        })

    @app.route("/api/stories/<int:story_id>", methods=["PUT"])
    def edit_story(story_id):
        data = request.get_json(silent=True) or {}

        try:
            result = update_story(
                story_id=story_id,
                champion_name=data.get("champion_name"),
                title=data.get("title"),
                body=data.get("body"),
                source_url=data.get("source_url"),
                registration_method=data.get(
                    "registration_method",
                    "url",
                ),
                allow_duplicate=data.get(
                    "allow_duplicate",
                    False,
                ),
            )

            if not result["success"]:
                if result.get("duplicate"):
                    return jsonify(result), 409

                if result.get("error") == "Story not found.":
                    return jsonify(result), 404

                return jsonify(result), 400

            return jsonify(result), 200

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/api/stories/<int:story_id>", methods=["DELETE"])
    def remove_story(story_id):
        try:
            deleted = delete_story(story_id)

            if not deleted:
                return jsonify({
                    "success": False,
                    "error": "Story not found.",
                }), 404

            return jsonify({
                "success": True,
                "message": "Story deleted successfully.",
            }), 200

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/dictionary")
    def dictionary():
        return render_template("dictionary.html")

    @app.route("/network")
    def network():
        return render_template("network.html")

    return app