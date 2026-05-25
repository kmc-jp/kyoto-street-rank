from sqlalchemy import text

from .extensions import db


def ensure_schema():
    columns = db.session.execute(text("PRAGMA table_info(streets)")).fetchall()
    column_names = {column[1] for column in columns}
    if "orientation" not in column_names:
        db.session.execute(text("ALTER TABLE streets ADD COLUMN orientation VARCHAR(20)"))
        db.session.commit()
