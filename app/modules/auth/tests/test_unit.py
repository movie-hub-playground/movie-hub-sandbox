import pytest, time
from flask import url_for

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.repositories import UserProfileRepository


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login", data=dict(email="bademail@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="basspassword"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_service_create_with_profie_success(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "service_test@example.com", "password": "test1234"}

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "test@example.com", "password": ""}

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0

def test_login_success_resets_attempts(test_client):
    
    test_client.post("/login", data=dict(email="test@example.com", password="bad"), follow_redirects=True)

    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("public.index")
    
    test_client.get("/logout", follow_redirects=True)

def test_login_block_after_max_attempts(test_client):
    
    i = 0
    while i < 3:
        response = test_client.post(
            "/login", data=dict(email="test@example.com", password="wrongpassword"), follow_redirects=True
        )
        i += 1
        assert response.request.path == url_for("auth.login")
        

    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="test1234"),  # aunque sea correcta, ya está bloqueado
        follow_redirects=True,
    )

    assert b"Too many requests" in response.data
    
def test_email_validation_flow(test_client):
    """Test the complete email validation flow"""
    
    signup_response = test_client.post(
        "/signup",
        data=dict(name="Test", surname="Validator", email="validator@example.com", password="valid1234"),
        follow_redirects=True
    )
    assert signup_response.request.path == url_for("auth.email_validation")
    
    
    with test_client.session_transaction() as session:
        assert 'verification_key' in session
        verification_code = session['verification_key']
        assert verification_code == "123456"
    
    
    validation_response = test_client.post(
        "/email_validation",
        data=dict(key="123456"),
        follow_redirects=True
    )
    assert validation_response.request.path == url_for("public.index")
    
    
    with test_client.session_transaction() as session:
        assert 'verification_key' not in session
        assert 'email' not in session
        assert 'password' not in session

def test_email_validation_wrong_code(test_client):
    """Test email validation with incorrect verification code"""

    test_client.post(
        "/signup",
        data=dict(name="Wrong", surname="Code", email="wrong@example.com", password="wrong1234"),
        follow_redirects=True
    )
    
    
    response = test_client.post(
        "/email_validation",
        data=dict(key="000000"),  
        follow_redirects=True
    )
    assert b'key does not match' in response.data.lower()
    assert response.request.path == url_for("auth.email_validation")

def test_login_success_resets_attempts(test_client):
    
    test_client.post(
        "/signup",
        data=dict(name="Login", surname="Test", email="login@example.com", password="login1234"),
        follow_redirects=True
    )
    test_client.post(
        "/email_validation",
        data=dict(key="123456"),
        follow_redirects=True
    )
    test_client.get("/logout", follow_redirects=True)
    
    
    test_client.post("/login", data=dict(email="login@example.com", password="bad"), follow_redirects=True)