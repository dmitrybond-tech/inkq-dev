"""Tests for artist profile and public artist endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base, get_db
from app.config import settings
from app.models.user import User, AccountType
from app.models.artist import Artist
from app.models.portfolio import PortfolioImage


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


def signup_and_signin_artist(client: TestClient, email: str = "artist@example.com") -> str:
  """Helper to create an artist user and return access token."""
  signup_resp = client.post(
    "/api/v1/auth/signup",
    json={
      "email": email,
      "password": "password123",
      "username": "testartist",
      "account_type": "artist",
    },
  )
  assert signup_resp.status_code == 201

  signin_resp = client.post(
    "/api/v1/auth/signin",
    json={"login": email, "password": "password123"},
  )
  assert signin_resp.status_code == 200
  data = signin_resp.json()
  return data["access_token"]


def test_get_me_artist_profile_initial(client, db_session):
  """GET /artists/me returns artist profile with steps for an artist user."""
  token = signup_and_signin_artist(client)

  resp = client.get(
    "/api/v1/artists/me",
    headers={"Authorization": f"Bearer {token}"},
  )

  assert resp.status_code == 200
  data = resp.json()
  assert data["username"] == "testartist"
  assert data["onboarding_completed"] is False
  assert "steps" in data
  steps = data["steps"]
  assert "about_complete" in steps
  assert "media_complete" in steps
  assert "portfolio_complete" in steps
  assert "wannado_complete" in steps
  assert 1 <= steps["first_incomplete_step"] <= 4


def test_put_me_updates_profile_and_onboarding(client, db_session):
  """PUT /artists/me updates artist metadata and onboarding_completed flag."""
  token = signup_and_signin_artist(client, email="artist2@example.com")

  payload = {
    "about": "I love blackwork and geometric tattoos.",
    "styles": ["blackwork", "geometric"],
    "city": "Berlin",
    "session_price": 200,
    "instagram": "@ink_master",
    "telegram": "@ink_master_tg",
    "onboarding_completed": True,
  }

  resp = client.put(
    "/api/v1/artists/me",
    headers={"Authorization": f"Bearer {token}"},
    json=payload,
  )

  assert resp.status_code == 200
  data = resp.json()
  assert data["about"] == payload["about"]
  assert data["styles"] == payload["styles"]
  assert data["city"] == payload["city"]
  assert data["session_price"] == payload["session_price"]
  assert data["instagram"] == payload["instagram"]
  assert data["telegram"] == payload["telegram"]
  assert data["onboarding_completed"] is True

  # Verify DB state
  user = db_session.query(User).filter(User.email == "artist2@example.com").first()
  assert user is not None
  assert user.onboarding_completed is True
  assert user.artist is not None
  assert user.artist.city == "Berlin"


def test_get_public_artist_profile(client, db_session):
  """GET /artists/{username} returns public data including portfolio and wannado."""
  # Create user and artist directly
  user = User(
    email="public@example.com",
    password_hash="hash",
    username="publicartist",
    account_type=AccountType.ARTIST,
    onboarding_completed=True,
  )
  db_session.add(user)
  db_session.flush()

  artist = Artist(user_id=user.id, about="Public artist", styles=["traditional"], city="Paris")
  db_session.add(artist)
  db_session.flush()

  # Add portfolio and wannado images
  p1 = PortfolioImage(
    user_id=user.id,
    kind="portfolio",
    url="/media/p1.webp",
    width=1000,
    height=1000,
    mime_type="image/webp",
  )
  w1 = PortfolioImage(
    user_id=user.id,
    kind="wannado",
    url="/media/w1.webp",
    width=1000,
    height=1000,
    mime_type="image/webp",
  )
  db_session.add(p1)
  db_session.add(w1)
  db_session.commit()

  resp = client.get("/api/v1/artists/publicartist")
  assert resp.status_code == 200
  data = resp.json()
  assert data["username"] == "publicartist"
  assert data["about"] == "Public artist"
  assert data["styles"] == ["traditional"]
  assert data["city"] == "Paris"
  assert len(data["portfolio"]) == 1
  assert len(data["wannado"]) == 1


def test_get_public_artist_not_found(client, db_session):
  """GET /artists/{username} returns 404 for unknown artist."""
  resp = client.get("/api/v1/artists/unknown-artist")
  assert resp.status_code == 404


