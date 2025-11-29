from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService
from app.modules.profile.repositories import UserProfileRepository
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result, errors, "profile.edit_profile", "Profile updated successfully", "profile/edit.html", form
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/admin/profiles", methods=["GET"])
@login_required
def admin_list_profiles():
    if current_user.email != "user1@example.com":
        return render_template("401.html"), 401

    page = request.args.get("page", 1, type=int)
    per_page = 10

    repo = UserProfileRepository()
    pagination = repo.session.query(UserProfile).order_by(UserProfile.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    user_ids = [p.user_id for p in pagination.items]
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}

    return render_template(
        "profile/admin_profiles.html",
        profiles=pagination.items,
        users=users,
        pagination=pagination,
    )


@profile_bp.route("/admin/profiles/<int:profile_id>/delete", methods=["POST"])
@login_required
def admin_delete_profile(profile_id):
    if current_user.email != "user1@example.com":
        return render_template("401.html"), 401

    repo = UserProfileRepository()
    profile = repo.get_by_id(profile_id)
    if not profile:
        return render_template("404.html"), 404

    user = User.query.get(profile.user_id)
    try:
        if user:
            db.session.delete(user)
        db.session.delete(profile)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return render_template("500.html"), 500

    return redirect(url_for("profile.admin_list_profiles"))