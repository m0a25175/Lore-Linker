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

from lore_linker.services.dictionary_manager import (
    get_dictionary_terms,
    get_dictionary_term_by_id,
    add_dictionary_term,
    update_dictionary_term,
    delete_dictionary_term,
    get_dictionary_term_usage_count,
    get_dictionary_overview,
    get_dictionary_overview,
    add_dictionary_terms_bulk,
)

from lore_linker.services.dictionary_collector import (
    collect_dictionary_candidates,
)

from lore_linker.services.analysis_engine import (
    analyze_network,
    get_latest_analysis,
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

    @app.route("/api/dictionary/candidates", methods=["GET"])
    def list_dictionary_candidates():
        try:
            result = collect_dictionary_candidates()

            return jsonify(result), 200

        except RuntimeError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 500

        except Exception:
            app.logger.exception(
                "Failed to collect dictionary candidates."
            )

            return jsonify({
                "success": False,
                "error": "Failed to collect dictionary candidates.",
            }), 500

    @app.route(
        "/api/dictionary/candidates/register",
        methods=["POST"],
    )
    def register_dictionary_candidates():
        data = request.get_json(silent=True) or {}
        terms = data.get("terms")

        if not isinstance(terms, list):
            return jsonify({
                "success": False,
                "error": "Terms must be provided as a list.",
            }), 400

        if len(terms) == 0:
            return jsonify({
                "success": False,
                "error": "Please select at least one term.",
            }), 400

        if len(terms) > 1000:
            return jsonify({
                "success": False,
                "error": "You can register up to 1000 terms at once.",
            }), 400

        try:
            result = add_dictionary_terms_bulk(terms)

            return jsonify({
                "success": True,
                **result,
            }), 200

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/api/dictionary/terms", methods=["GET"])
    def list_dictionary_terms():
        terms = get_dictionary_terms()

        return jsonify({
            "success": True,
            "terms": terms,
        })

    @app.route("/api/dictionary/terms", methods=["POST"])
    def create_dictionary_term():
        data = request.get_json(silent=True) or {}

        try:
            term = add_dictionary_term(data.get("term"))

            return jsonify({
                "success": True,
                "term": term,
            }), 201

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

    @app.route("/api/dictionary/terms/<int:term_id>", methods=["GET"])
    def retrieve_dictionary_term(term_id):
        term = get_dictionary_term_by_id(term_id)

        if term is None:
            return jsonify({
                "success": False,
                "error": "Dictionary term not found.",
            }), 404

        term["usage_count"] = get_dictionary_term_usage_count(term_id)

        return jsonify({
            "success": True,
            "term": term,
        })

    @app.route("/api/dictionary/terms/<int:term_id>", methods=["PUT"])
    def edit_dictionary_term(term_id):
        data = request.get_json(silent=True) or {}

        try:
            term = update_dictionary_term(
                term_id=term_id,
                term=data.get("term"),
            )

            return jsonify({
                "success": True,
                "term": term,
            }), 200

        except ValueError as error:
            status_code = (
                404
                if str(error).startswith("Dictionary term not found:")
                else 400
            )

            return jsonify({
                "success": False,
                "error": str(error),
            }), status_code

    @app.route("/api/dictionary/terms/<int:term_id>", methods=["DELETE"])
    def remove_dictionary_term(term_id):
        term = get_dictionary_term_by_id(term_id)

        if term is None:
            return jsonify({
                "success": False,
                "error": "Dictionary term not found.",
            }), 404

        usage_count = get_dictionary_term_usage_count(term_id)

        deleted = delete_dictionary_term(term_id)

        if not deleted:
            return jsonify({
                "success": False,
                "error": "Dictionary term could not be deleted.",
            }), 500

        return jsonify({
            "success": True,
            "message": "Dictionary term deleted successfully.",
            "deleted_term": term["term"],
            "deleted_usage_count": usage_count,
        }), 200

    @app.route("/api/dictionary/overview", methods=["GET"])
    def dictionary_overview():
        overview = get_dictionary_overview()

        return jsonify({
            "success": True,
            "overview": overview,
        })

    @app.route("/dictionary")
    def dictionary():
        return render_template("dictionary.html")

    @app.route("/network")
    def network():
        champions = get_registered_champions()

        return render_template(
            "network.html",
            champions=champions,
        )

    @app.route("/api/analysis/run", methods=["POST"])
    def run_analysis():
        data = request.get_json(silent=True) or {}

        try:
            result = analyze_network(
                selected_champions=data.get("selected_champions"),
                threshold=data.get("threshold", 10),
            )

            return jsonify(result), 200

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

        except Exception:
            app.logger.exception("Analysis execution failed.")

            return jsonify({
                "success": False,
                "error": "Analysis execution failed.",
            }), 500

    @app.route("/api/analysis/state", methods=["GET"])
    def analysis_state():
        state = get_latest_analysis()

        return jsonify({
            "success": True,
            "state": state,
        }), 200

    @app.route("/api/analysis/export", methods=["GET"])
    def export_analysis():
        state = get_latest_analysis()

        if state is None or state["result"] is None:
            return jsonify({
                "success": False,
                "error": "No analysis result is available.",
            }), 404

        return jsonify({
            "success": True,
            "format": "lore-linker-analysis",
            "version": 1,
            "selected_champions": state["selected_champions"],
            "threshold": state["threshold"],
            "result": state["result"],
            "updated_at": state["updated_at"],
        }), 200

    @app.route("/api/analysis/import", methods=["POST"])
    def import_analysis():
        data = request.get_json(silent=True) or {}

        if data.get("format") != "lore-linker-analysis":
            return jsonify({
                "success": False,
                "error": "Unsupported analysis file format.",
            }), 400

        if data.get("version") != 1:
            return jsonify({
                "success": False,
                "error": "Unsupported analysis file version.",
            }), 400

        try:
            result = analyze_network(
                selected_champions=data.get("selected_champions"),
                threshold=data.get("threshold", 10),
            )

            return jsonify({
                "success": True,
                "message": "Analysis conditions restored and analysis completed.",
                "result": result,
            }), 200

        except ValueError as error:
            return jsonify({
                "success": False,
                "error": str(error),
            }), 400

        except Exception:
            app.logger.exception("Analysis import failed.")

            return jsonify({
                "success": False,
                "error": "Failed to restore analysis.",
            }), 500

    return app