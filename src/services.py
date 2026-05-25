from sqlalchemy import or_

from .extensions import db
from .models import Intersection, Street


def list_street_names():
    streets = Street.query.order_by(Street.name).all()
    return [street.name for street in streets]


def count_intersections_by_street():
    counts = {}
    intersections = Intersection.query.all()
    for intersection in intersections:
        counts[intersection.winner_street_id] = counts.get(intersection.winner_street_id, 0) + 1
        counts[intersection.loser_street_id] = counts.get(intersection.loser_street_id, 0) + 1
    return counts


def save_intersection(name, winner_name, loser_name, intersection=None):
    name = normalize_name(name)
    winner_name = normalize_name(winner_name)
    loser_name = normalize_name(loser_name)

    if not name or not winner_name or not loser_name:
        return "交差点名、強い通り、弱い通りをすべて入力してください"
    if winner_name == loser_name:
        return "強い通りと弱い通りには別の通りを入力してください"

    duplicate_name = Intersection.query.filter(Intersection.name == name)
    if intersection:
        duplicate_name = duplicate_name.filter(Intersection.id != intersection.id)
    if duplicate_name.first():
        return "同じ交差点名が既に存在します"

    old_street_ids = set()
    if intersection:
        old_street_ids = {intersection.winner_street_id, intersection.loser_street_id}

    winner = find_or_create_street(winner_name)
    loser = find_or_create_street(loser_name)
    db.session.flush()

    pair_key = make_pair_key(winner.id, loser.id)
    duplicate_pair = Intersection.query.filter(Intersection.pair_key == pair_key)
    if intersection:
        duplicate_pair = duplicate_pair.filter(Intersection.id != intersection.id)
    if duplicate_pair.first():
        db.session.rollback()
        return "同じ通りの組み合わせの交差点が既に存在します"

    if intersection is None:
        intersection = Intersection()
        db.session.add(intersection)

    intersection.name = name
    intersection.winner = winner
    intersection.loser = loser
    intersection.pair_key = pair_key

    db.session.flush()
    delete_orphan_streets(old_street_ids)
    db.session.commit()
    return None


def delete_intersection(intersection):
    street_ids = {intersection.winner_street_id, intersection.loser_street_id}
    db.session.delete(intersection)
    db.session.flush()
    delete_orphan_streets(street_ids)
    db.session.commit()


def update_street_name(street, name):
    name = normalize_name(name)
    if not name:
        return "通り名を入力してください"

    duplicate = Street.query.filter(Street.name == name, Street.id != street.id).first()
    if duplicate:
        return "同じ通り名が既に存在します"

    street.name = name
    db.session.commit()
    return None


def delete_street_and_intersections(street):
    intersections = Intersection.query.filter(
        or_(Intersection.winner_street_id == street.id, Intersection.loser_street_id == street.id)
    ).all()
    affected_street_ids = {street.id}

    for intersection in intersections:
        affected_street_ids.add(intersection.winner_street_id)
        affected_street_ids.add(intersection.loser_street_id)
        db.session.delete(intersection)

    db.session.delete(street)
    db.session.flush()
    delete_orphan_streets(affected_street_ids)
    db.session.commit()


def find_or_create_street(name):
    street = Street.query.filter_by(name=name).first()
    if street:
        return street

    street = Street(name=name)
    db.session.add(street)
    return street


def delete_orphan_streets(street_ids):
    for street_id in street_ids:
        if not street_id:
            continue
        has_intersection = Intersection.query.filter(
            or_(Intersection.winner_street_id == street_id, Intersection.loser_street_id == street_id)
        ).first()
        if not has_intersection:
            street = db.session.get(Street, street_id)
            if street:
                db.session.delete(street)


def make_pair_key(left_id, right_id):
    low, high = sorted([left_id, right_id])
    return f"{low}:{high}"


def normalize_name(value):
    if value is None:
        return ""
    return value.strip()
