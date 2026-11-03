from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def story():
        return render_template("story.html")

    @app.route("/dictionary")
    def dictionary():
        return render_template("dictionary.html")

    @app.route("/network")
    def network():
        return render_template("network.html")

    return app