"""Tests for authentication and signup flow."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base, get_db
from app.models.user import User, AccountType
from app.models.artist import Artist
from app.models.studio import Studio
from app.models.model import Model
from app.models.session import Session
from app.config import settings

# Create test database (for local dev we reuse the main DB URL)
SQLALCHEMY_TEST_DATABASE_URL = settings.inkq_pg_url
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_signup_artist(client, db_session):
    """Test signup as artist creates User + Artist in single transaction."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "artist@example.com",
            "password": "password123",
            "username": "testartist",
            "account_type": "artist"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "artist@example.com"
    assert data["username"] == "testartist"
    assert data["account_type"] == "artist"
    assert data["onboarding_completed"] is False
    
    # Verify User exists
    user = db_session.query(User).filter(User.email == "artist@example.com").first()
    assert user is not None
    assert user.account_type == AccountType.ARTIST
    
    # Verify Artist role exists
    artist = db_session.query(Artist).filter(Artist.user_id == user.id).first()
    assert artist is not None
    assert artist.user_id == user.id
    
    # Verify no other roles exist
    studio = db_session.query(Studio).filter(Studio.user_id == user.id).first()
    model = db_session.query(Model).filter(Model.user_id == user.id).first()
    assert studio is None
    assert model is None


def test_signup_studio(client, db_session):
    """Test signup as studio creates User + Studio in single transaction."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "studio@example.com",
            "password": "password123",
            "username": "teststudio",
            "account_type": "studio"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["account_type"] == "studio"
    
    # Verify User and Studio exist
    user = db_session.query(User).filter(User.email == "studio@example.com").first()
    assert user is not None
    assert user.account_type == AccountType.STUDIO
    
    studio = db_session.query(Studio).filter(Studio.user_id == user.id).first()
    assert studio is not None
    
    # Verify no other roles exist
    artist = db_session.query(Artist).filter(Artist.user_id == user.id).first()
    model = db_session.query(Model).filter(Model.user_id == user.id).first()
    assert artist is None
    assert model is None


def test_signup_model(client, db_session):
    """Test signup as model creates User + Model in single transaction."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "model@example.com",
            "password": "password123",
            "username": "testmodel",
            "account_type": "model"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["account_type"] == "model"
    
    # Verify User and Model exist
    user = db_session.query(User).filter(User.email == "model@example.com").first()
    assert user is not None
    assert user.account_type == AccountType.MODEL
    
    model = db_session.query(Model).filter(Model.user_id == user.id).first()
    assert model is not None
    
    # Verify no other roles exist
    artist = db_session.query(Artist).filter(Artist.user_id == user.id).first()
    studio = db_session.query(Studio).filter(Studio.user_id == user.id).first()
    assert artist is None
    assert studio is None


def test_signup_invalid_account_type(client, db_session):
    """Test signup with invalid account_type returns 400."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "invalid@example.com",
            "password": "password123",
            "username": "invalid",
            "account_type": "invalid_type"
        }
    )
    
    assert response.status_code == 400
    assert "Invalid account_type" in response.json()["detail"]


def test_signup_duplicate_email(client, db_session):
    """Test signup with duplicate email returns 400."""
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "username": "user1",
            "account_type": "artist"
        }
    )
    
    # Second signup with same email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "username": "user2",
            "account_type": "studio"
        }
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_signup_duplicate_username(client, db_session):
    """Test signup with duplicate username returns 400."""
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user1@example.com",
            "password": "password123",
            "username": "duplicate",
            "account_type": "artist"
        }
    )
    
    # Second signup with same username
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user2@example.com",
            "password": "password123",
            "username": "duplicate",
            "account_type": "studio"
        }
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_role_invariants(client, db_session):
    """Test that role invariants are maintained after signup."""
    # Create artist
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "invariant@example.com",
            "password": "password123",
            "username": "invariant",
            "account_type": "artist"
        }
    )
    assert response.status_code == 201
    
    # Verify invariant: account_type = 'artist' => artist is not None
    user = db_session.query(User).filter(User.email == "invariant@example.com").first()
    assert user.account_type == AccountType.ARTIST
    assert user.artist is not None
    assert user.studio is None
    assert user.model is None


def test_signin_success(client, db_session):
    """Test successful signin creates session and returns token."""
    # Create user via signup
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "signin@example.com",
            "password": "password123",
            "username": "signinuser",
            "account_type": "artist"
        }
    )
    assert signup_response.status_code == 201
    
    # Sign in
    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "signin@example.com",
            "password": "password123"
        }
    )
    
    assert signin_response.status_code == 200
    data = signin_response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "signin@example.com"
    assert data["user"]["username"] == "signinuser"
    
    # Verify session was created
    token = data["access_token"]
    session = db_session.query(Session).filter(Session.id == token).first()
    assert session is not None
    assert session.user_id == data["user"]["id"]


def test_signin_with_username(client, db_session):
    """Test signin with username instead of email."""
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "username@example.com",
            "password": "password123",
            "username": "testusername",
            "account_type": "studio"
        }
    )
    
    # Sign in with username
    response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "testusername",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "testusername"


def test_signin_wrong_password(client, db_session):
    """Test signin with wrong password returns 401."""
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrongpass@example.com",
            "password": "password123",
            "username": "wrongpass",
            "account_type": "model"
        }
    )
    
    # Sign in with wrong password
    response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "wrongpass@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


def test_signin_invalid_user(client, db_session):
    """Test signin with non-existent user returns 401."""
    response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


def test_auth_me_success(client, db_session):
    """Test /auth/me returns user data for valid token."""
    # Create user and sign in
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "me@example.com",
            "password": "password123",
            "username": "meuser",
            "account_type": "artist"
        }
    )
    
    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "me@example.com",
            "password": "password123"
        }
    )
    token = signin_response.json()["access_token"]
    
    # Call /auth/me
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"
    assert data["account_type"] == "artist"
    
    # Verify last_seen_at was updated
    session = db_session.query(Session).filter(Session.id == token).first()
    assert session.last_seen_at is not None


def test_auth_me_invalid_token(client, db_session):
    """Test /auth/me with invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_auth_me_no_token(client, db_session):
    """Test /auth/me without token returns 401."""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


def test_signout_success(client, db_session):
    """Test signout deletes session."""
    # Create user and sign in
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "signout@example.com",
            "password": "password123",
            "username": "signoutuser",
            "account_type": "studio"
        }
    )
    
    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "signout@example.com",
            "password": "password123"
        }
    )
    token = signin_response.json()["access_token"]
    
    # Verify session exists
    session = db_session.query(Session).filter(Session.id == token).first()
    assert session is not None
    
    # Sign out
    signout_response = client.post(
        "/api/v1/auth/signout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert signout_response.status_code == 204
    
    # Verify session was deleted
    db_session.expire_all()  # Refresh all objects
    deleted_session = db_session.query(Session).filter(Session.id == token).first()
    assert deleted_session is None
    
    # Verify subsequent /auth/me calls fail
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 401


def test_signup_and_signin_with_long_password(client, db_session):
    """User can signup and signin with a long password without 500 errors."""
    long_password = "L" * 120

    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "longpass@example.com",
            "password": long_password,
            "username": "longpassuser",
            "account_type": "artist",
        },
    )

    assert signup_response.status_code == 201

    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "longpass@example.com",
            "password": long_password,
        },
    )

    assert signin_response.status_code == 200
    data = signin_response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "longpass@example.com"
    # Ensure we never leak low-level bcrypt error messages
    assert "password cannot be longer than 72 bytes" not in signup_response.text
    assert "password cannot be longer than 72 bytes" not in signin_response.text


def test_signup_and_signin_with_long_unicode_password(client, db_session):
    """User can signup and signin with a long UTF-8 password without 500 errors."""
    # Use characters that are multiple bytes in UTF-8 to exceed 72 bytes easily
    long_unicode_password = "🔒" * 40  # 40 * 4 bytes = 160 bytes approximately

    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "longunicode@example.com",
            "password": long_unicode_password,
            "username": "longunicodeuser",
            "account_type": "artist",
        },
    )

    assert signup_response.status_code == 201

    signin_response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "longunicode@example.com",
            "password": long_unicode_password,
        },
    )

    assert signin_response.status_code == 200
    data = signin_response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "longunicode@example.com"
    # Ensure no raw bcrypt 72-byte error message is exposed
    assert "password cannot be longer than 72 bytes" not in signup_response.text
    assert "password cannot be longer than 72 bytes" not in signin_response.text


def test_signup_rejects_too_short_password(client, db_session):
    """Signup should reject passwords shorter than the minimum."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "shortpass@example.com",
            "password": "short",
            "username": "shortuser",
            "account_type": "artist",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    # Pydantic v2 returns a list of error objects
    assert any(
        "Password must be between" in err.get("msg", "")
        for err in detail
    )


def test_signup_rejects_too_long_password(client, db_session):
    """Signup should reject passwords longer than the maximum."""
    long_password = "X" * 129

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "toolong@example.com",
            "password": long_password,
            "username": "toolonguser",
            "account_type": "artist",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        "Password must be between" in err.get("msg", "")
        for err in detail
    )


def test_signin_rejects_too_short_password(client, db_session):
    """Signin should reject passwords that are too short at validation level."""
    # First create a valid user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "signinshort@example.com",
            "password": "validpassword",
            "username": "signinshortuser",
            "account_type": "artist",
        },
    )

    response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "signinshort@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        "Password must be between" in err.get("msg", "")
        for err in detail
    )


def test_signin_rejects_too_long_password(client, db_session):
    """Signin should reject passwords that are too long at validation level."""
    long_password = "P" * 120

    # First create a valid user with a normal password
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "signinlong@example.com",
            "password": "validpassword",
            "username": "signinlonguser",
            "account_type": "artist",
        },
    )

    too_long_password = "P" * 129
    response = client.post(
        "/api/v1/auth/signin",
        json={
            "login": "signinlong@example.com",
            "password": too_long_password,
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        "Password must be between" in err.get("msg", "")
        for err in detail
    )
