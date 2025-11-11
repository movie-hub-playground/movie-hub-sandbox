import os
from datetime import datetime, timedelta
from flask import session
from flask_login import current_user, login_user

from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

from flask import current_app
from flask_mail import Message
from app import mail


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()
        self.MAX_ATTEMPTS = 3
        self.BASE_BLOCK_TIME = 30

    def login(self, email, password, remember=True):
        now = datetime.utcnow()
        attempts = session.get("login_attempts", 0)
        blocked_until = session.get("blocked_until")

        if blocked_until and now < datetime.fromisoformat(blocked_until):
            remaining = int((datetime.fromisoformat(blocked_until) - now).total_seconds())
            return False, 0, remaining

        user = self.repository.get_by_email(email)

        if user and user.check_password(password):
            login_user(user, remember=remember)
            session.pop("login_attempts", None)
            session.pop("blocked_until", None)
            return True, self.MAX_ATTEMPTS, 0

        attempts += 1
        session["login_attempts"] = attempts

        if attempts >= self.MAX_ATTEMPTS:
            block_time = self.BASE_BLOCK_TIME * (2 ** (attempts - self.MAX_ATTEMPTS))
            blocked_until_dt = now + timedelta(seconds=block_time)
            session["blocked_until"] = blocked_until_dt.isoformat()
            return False, 0, int(block_time)

        return False, self.MAX_ATTEMPTS - attempts, 0

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()

            verification_code = "123456"  # Futuro problema -> crear codigo aleatorio
            self.send_email(email, verification_code)

        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))

    def send_email(self, to_email, verification_code):
        try:
            print("=== Email Configuration ===")
            print(f"MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
            print(f"MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
            print(f"MAIL_USE_SSL: {current_app.config.get('MAIL_USE_SSL')}")
            print(f"MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
            msg = Message(
                'Verify your email - MovieHub',
                sender=current_app.config.get('MAIL_USERNAME'),
                recipients=[to_email]
            )
            msg.body = f'Your verification code is: {verification_code}'
            msg.html = f'''
                <h1>Welcome to MovieHub!</h1>
                <p>Your verification code is: <strong>{verification_code}</strong></p>
            '''
            mail.send(msg)
            print("Email sent successfully!")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            current_app.logger.error(f"Error sending email: {str(e)}")
            return False