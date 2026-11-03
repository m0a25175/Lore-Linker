from flask import Flask, render_template

from lore_linker.services.database import initialize_database
from lore_linker.services.champion_data import get_registered_champions

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

    @app.route("/dictionary")
    def dictionary():
        return render_template("dictionary.html")

    @app.route("/network")
    def network():
        return render_template("network.html")

    return app