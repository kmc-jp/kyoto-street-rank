from sqlalchemy import CheckConstraint, UniqueConstraint

from .extensions import db


class Street(db.Model):
    __tablename__ = "streets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    orientation = db.Column(db.String(20), nullable=True)


class Intersection(db.Model):
    __tablename__ = "intersections"
    __table_args__ = (
        UniqueConstraint("name", name="uq_intersections_name"),
        UniqueConstraint("pair_key", name="uq_intersections_pair_key"),
        CheckConstraint("winner_street_id != loser_street_id", name="ck_different_streets"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    pair_key = db.Column(db.String(80), nullable=False)
    winner_street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)
    loser_street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)

    winner = db.relationship("Street", foreign_keys=[winner_street_id])
    loser = db.relationship("Street", foreign_keys=[loser_street_id])
