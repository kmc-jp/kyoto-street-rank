from flask import flash, redirect, render_template, request, url_for
from sqlalchemy.orm import aliased

from .graph_view import build_graph_view
from .models import Intersection, Street
from .ranking import calculate_ranking
from .services import (
    count_intersections_by_street,
    delete_intersection,
    delete_street_and_intersections,
    list_street_names,
    save_intersection,
    update_street_name,
)


def register_routes(app):
    @app.route("/")
    def ranking():
        intersections = Intersection.query.order_by(Intersection.name).all()
        ranks = calculate_ranking(intersections)
        return render_template("ranking.html", ranks=ranks, intersections=intersections)

    @app.route("/graph")
    def graph():
        intersections = Intersection.query.order_by(Intersection.name).all()
        graph_view = build_graph_view(intersections)
        return render_template("graph.html", graph=graph_view)

    @app.route("/intersections")
    def intersections_index():
        selected_street = request.args.get("street", "").strip()
        intersections_query = Intersection.query

        if selected_street:
            winner = aliased(Street)
            loser = aliased(Street)
            intersections_query = (
                intersections_query.join(winner, Intersection.winner)
                .join(loser, Intersection.loser)
                .filter((winner.name == selected_street) | (loser.name == selected_street))
            )

        intersections = intersections_query.order_by(Intersection.name).all()
        return render_template(
            "intersections/index.html",
            intersections=intersections,
            street_names=list_street_names(),
            selected_street=selected_street,
        )

    @app.route("/intersections/new", methods=["GET", "POST"])
    def intersections_new():
        return_street = request.values.get("street", "").strip()
        if request.method == "POST":
            error = save_intersection(
                request.form.get("name"),
                request.form.get("winner"),
                request.form.get("loser"),
            )
            if error:
                flash(error, "error")
                return render_intersection_form(None, request.form, return_street)

            flash("交差点を追加しました", "success")
            return redirect(intersections_index_url(return_street))

        return render_intersection_form(None, {}, return_street)

    @app.route("/intersections/<int:intersection_id>/edit", methods=["GET", "POST"])
    def intersections_edit(intersection_id):
        intersection = Intersection.query.get_or_404(intersection_id)
        return_street = request.values.get("street", "").strip()
        if request.method == "POST":
            error = save_intersection(
                request.form.get("name"),
                request.form.get("winner"),
                request.form.get("loser"),
                intersection,
            )
            if error:
                flash(error, "error")
                return render_intersection_form(intersection, request.form, return_street)

            flash("交差点を更新しました", "success")
            return redirect(intersections_index_url(return_street))

        form = {
            "name": intersection.name,
            "winner": intersection.winner.name,
            "loser": intersection.loser.name,
        }
        return render_intersection_form(intersection, form, return_street)

    @app.route("/intersections/<int:intersection_id>/delete", methods=["POST"])
    def intersections_delete(intersection_id):
        intersection = Intersection.query.get_or_404(intersection_id)
        return_street = request.form.get("street", "").strip()
        delete_intersection(intersection)
        flash("交差点を削除しました", "success")
        return redirect(intersections_index_url(return_street))

    @app.route("/streets")
    def streets_index():
        streets = Street.query.order_by(Street.name).all()
        intersection_counts = count_intersections_by_street()
        return render_template("streets/index.html", streets=streets, intersection_counts=intersection_counts)

    @app.route("/streets/<int:street_id>/edit", methods=["GET", "POST"])
    def streets_edit(street_id):
        street = Street.query.get_or_404(street_id)
        if request.method == "POST":
            error = update_street_name(street, request.form.get("name"))
            if error:
                flash(error, "error")
                return render_template("streets/form.html", street=street)

            flash("通り名を更新しました", "success")
            return redirect(url_for("streets_index"))

        return render_template("streets/form.html", street=street)

    @app.route("/streets/<int:street_id>/delete", methods=["POST"])
    def streets_delete(street_id):
        street = Street.query.get_or_404(street_id)
        delete_street_and_intersections(street)
        flash("通りと関連する交差点を削除しました", "success")
        return redirect(url_for("streets_index"))


def render_intersection_form(intersection, form, return_street=""):
    return render_template(
        "intersections/form.html",
        intersection=intersection,
        form=form,
        return_street=return_street,
        street_names=list_street_names(),
    )


def intersections_index_url(street_name):
    if street_name:
        return url_for("intersections_index", street=street_name)
    return url_for("intersections_index")
