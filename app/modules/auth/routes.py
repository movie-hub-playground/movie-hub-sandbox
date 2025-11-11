from flask import redirect, render_template, request, url_for, session, make_response
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm, EmailValidationForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()

@auth_bp.route("/signup", methods=["GET", "POST"])
@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
            # Store email and password in session
            session['email'] = email
            session['password'] = form.password.data
            # Generate and store verification code
            verification_code = "123456"  # For testing
            session['verification_code'] = verification_code
            # Send verification email
            authentication_service.send_email(email, verification_code)
            # Redirect to email validation page
            print(f"Redirecting to email validation for {email}")  # Debug log
            return redirect(url_for('auth.email_validation'))
        except Exception as exc:
            print(f"Error in signup: {exc}")  # Debug log
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

    return render_template("auth/signup_form.html", form=form)



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        success, attempts_left, time_blocked = authentication_service.login(
            form.email.data, form.password.data
        )

        if success:
            return redirect(url_for("public.index"))

        if time_blocked > 0:
            error = f"Too many requests. Please wait {time_blocked} seconds"
        else:
            error = f"Invalid credentials. {attempts_left} {"attempts" if attempts_left > 1 else "attempt"} remaining"

        return render_template("auth/login_form.html", form=form, error=error)

    return render_template("auth/login_form.html", form=form)


@auth_bp.route('/email_validation', methods=['GET', 'POST'])
def email_validation():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    email = session.get('email')
    password = session.get('password')
    if not email or not password:
        return redirect(url_for('auth.login'))

    form = EmailValidationForm()

    if request.method == 'POST':
        entered_key = form.key.data.strip()
        stored_key = session.get('verification_key')
        print(f"Entered key: {entered_key}")
        print(f"Stored key: {stored_key}")

        if entered_key == stored_key:
            authentication_service.login(email, password)
            response = make_response(redirect(url_for('public.index')))

            session.pop('email', None)
            session.pop('password', None)
            session.pop('verification_key', None)
            return response

        return render_template(
            "auth/email_validation_form.html",
            form=form,
            error='The key does not match'
        )

    if request.method == 'GET':
        verification_key = "123456"
        session['verification_key'] = verification_key
        authentication_service.send_email(email, verification_key)
        

    return render_template('auth/email_validation_form.html', form=form, email=email)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))