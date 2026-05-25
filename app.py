from pathlib import Path

from flask import Flask

from extensions import db
from routes import register_routes

BASE_DIR = Path(__file__).resolve().parent


def create_app(database_uri=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or f"sqlite:///{BASE_DIR / 'kyoto_street_rank.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
