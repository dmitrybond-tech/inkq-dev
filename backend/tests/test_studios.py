"""Tests for studio profile, residents, booking and public studio endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base, get_db
from app.config import settings
from app.models.user import User, AccountType
from app.models.studio import Studio
from app.models.artist import Artist
from app.models.portfolio import PortfolioImage
from app.models.artist_studio_resident import ArtistStudioResident


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


def signup_and_signin_studio(client: TestClient, email: str = "studio@example.com") -> str:
    """Helper to create a studio user and return access token."""
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "username": "teststudio",
            "account_type": "studio",
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


def test_get_me_studio_profile_initial(client, db_session):
    """GET /studios/me returns studio profile for a studio user."""
    token = signup_and_signin_studio(client)

    resp = client.get(
        "/api/v1/studios/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "teststudio"
    # onboarding flag on studio table defaults to False
    assert data["onboarding_completed"] is False


def test_put_me_updates_studio_profile_and_onboarding(client, db_session):
    """PUT /studios/me updates studio metadata and onboarding_completed flag."""
    token = signup_and_signin_studio(client, email="studio2@example.com")

    payload = {
        "name": "InkQ Studio",
        "about": "Modern tattoo studio in the city center.",
        "city": "Berlin",
        "address": "Main street 1",
        "instagram": "@inkq_studio",
        "telegram": "@inkq_studio_tg",
        "vk": "https://vk.com/inkq",
        "session_price_label": "from 80€/session",
        "onboarding_completed": True,
    }

    resp = client.put(
        "/api/v1/studios/me",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == payload["name"]
    assert data["about"] == payload["about"]
    assert data["city"] == payload["city"]
    assert data["address"] == payload["address"]
    assert data["instagram"] == payload["instagram"]
    assert data["telegram"] == payload["telegram"]
    assert data["vk"] == payload["vk"]
    assert data["session_price_label"] == payload["session_price_label"]
    assert data["onboarding_completed"] is True

    # Verify DB state
    user = db_session.query(User).filter(User.email == "studio2@example.com").first()
    assert user is not None
    studio = db_session.query(Studio).filter(Studio.user_id == user.id).first()
    assert studio is not None
    assert studio.onboarding_completed is True
    assert studio.city == "Berlin"


def test_public_studio_endpoint_with_gallery_and_team(client, db_session):
    """GET /public/studios/{slug} returns studio info, gallery and team."""
    # Create studio user and studio
    user = User(
        email="studio-public@example.com",
        password_hash="hash",
        username="publicstudio",
        account_type=AccountType.STUDIO,
        onboarding_completed=True,
    )
    db_session.add(user)
    db_session.flush()

    studio = Studio(
        user_id=user.id,
        name="Public Studio",
        city="Paris",
        address="Studio street 5",
        instagram="@public_studio",
    )
    db_session.add(studio)
    db_session.flush()

    # Add gallery image
    img = PortfolioImage(
        user_id=user.id,
        kind="portfolio",
        url="/media/studio1.webp",
        width=1200,
        height=800,
        mime_type="image/webp",
    )
    db_session.add(img)

    # Create accepted resident artist
    artist_user = User(
        email="artist-public@example.com",
        password_hash="hash",
        username="artistresident",
        account_type=AccountType.ARTIST,
        onboarding_completed=True,
    )
    db_session.add(artist_user)
    db_session.flush()

    artist = Artist(
        user_id=artist_user.id,
        display_name="Resident Artist",
        styles=["blackwork"],
        city="Paris",
    )
    db_session.add(artist)
    db_session.flush()

    residency = ArtistStudioResident(
        studio_id=studio.id,
        artist_id=artist.id,
        status="accepted",
    )
    db_session.add(residency)
    db_session.commit()

    resp = client.get("/api/v1/public/studios/publicstudio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["studio"]["name"] == "Public Studio"
    assert data["studio"]["city"] == "Paris"
    assert len(data["gallery"]) == 1
    assert len(data["team"]) == 1
    assert data["aggregated_styles"] == ["blackwork"]


def test_public_studio_booking_general_and_artist_specific(client, db_session):
    """POST /public/studios/{slug}/booking works for general and artist_specific."""
    # Create studio and accepted artist resident similar to previous test
    user = User(
        email="studio-booking@example.com",
        password_hash="hash",
        username="bookingstudio",
        account_type=AccountType.STUDIO,
        onboarding_completed=True,
    )
    db_session.add(user)
    db_session.flush()

    studio = Studio(user_id=user.id, name="Booking Studio")
    db_session.add(studio)
    db_session.flush()

    artist_user = User(
        email="artist-booking@example.com",
        password_hash="hash",
        username="bookingartist",
        account_type=AccountType.ARTIST,
        onboarding_completed=True,
    )
    db_session.add(artist_user)
    db_session.flush()

    artist = Artist(user_id=artist_user.id)
    db_session.add(artist)
    db_session.flush()

    residency = ArtistStudioResident(
        studio_id=studio.id,
        artist_id=artist.id,
        status="accepted",
    )
    db_session.add(residency)
    db_session.commit()

    # General booking
    resp_general = client.post(
        "/api/v1/public/studios/bookingstudio/booking",
        json={
            "type": "general",
            "client_name": "Client One",
            "client_contact": "client@example.com",
            "comment": "General question",
        },
    )
    assert resp_general.status_code == 201
    data_general = resp_general.json()
    assert data_general["type"] == "general"
    assert data_general["artist_id"] is None

    # Artist specific booking
    resp_specific = client.post(
        "/api/v1/public/studios/bookingstudio/booking",
        json={
            "type": "artist_specific",
            "client_name": "Client Two",
            "client_contact": "client2@example.com",
            "comment": "For a specific artist",
            "artist_id": artist.id,
        },
    )
    assert resp_specific.status_code == 201
    data_specific = resp_specific.json()
    assert data_specific["type"] == "artist_specific"
    assert data_specific["artist_id"] == artist.id


