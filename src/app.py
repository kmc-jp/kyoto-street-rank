from pathlib import Path

from flask import Flask

from .extensions import db
from .routes import register_routes

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(database_uri=None):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config["SECRET_KEY"] = "dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or f"sqlite:///{PROJECT_ROOT / 'kyoto_street_rank.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
