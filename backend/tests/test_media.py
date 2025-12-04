"""Tests for media upload endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base, get_db
from app.models.user import User, AccountType
from app.models.session import Session as SessionModel
from app.models.portfolio import PortfolioImage
from app.config import settings
from datetime import datetime, timedelta
import secrets
import io
from PIL import Image
from app.routes.auth import hash_password

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


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        username="testuser",
        account_type=AccountType.ARTIST,
        onboarding_completed=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_session(db_session, test_user):
    """Create a test session."""
    token = secrets.token_urlsafe(32)
    session = SessionModel(
        id=token,
        user_id=test_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()
    return token


def create_test_image() -> io.BytesIO:
    """Create a test image in memory."""
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


def test_upload_avatar_invalid_file_type(client, test_session):
    """Test uploading avatar with invalid file type."""
    # Create a text file
    files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    response = client.post("/api/v1/media/artists/me/avatar", files=files, headers=headers)
    
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_avatar_success(client, db_session, test_user, test_session):
    """Test successful avatar upload."""
    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    response = client.post("/api/v1/media/artists/me/avatar", files=files, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["width"] == 400
    assert data["height"] == 400
    
    # Verify user record was updated
    db_session.refresh(test_user)
    assert test_user.avatar_url is not None
    assert test_user.avatar_url == data["url"]


def test_upload_avatar_unauthorized(client):
    """Test uploading avatar without authentication."""
    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    
    response = client.post("/api/v1/media/artists/me/avatar", files=files)
    
    assert response.status_code == 401


def test_upload_avatar_wrong_role(client, db_session, test_user, test_session):
    """Test uploading avatar with wrong account type."""
    # Change user to studio
    test_user.account_type = AccountType.STUDIO
    db_session.commit()
    
    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    response = client.post("/api/v1/media/artists/me/avatar", files=files, headers=headers)
    
    assert response.status_code == 403


def test_upload_banner_success(client, db_session, test_user, test_session):
    """Test successful banner upload."""
    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    response = client.post("/api/v1/media/artists/me/banner", files=files, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["width"] == 1584
    assert data["height"] == 396
    
    # Verify user record was updated
    db_session.refresh(test_user)
    assert test_user.banner_url is not None
    assert test_user.banner_url == data["url"]


def test_upload_portfolio_success(client, db_session, test_user, test_session):
    """Test successful portfolio upload."""
    img1_bytes = create_test_image()
    img2_bytes = create_test_image()
    
    files = [
        ("files", ("test1.jpg", img1_bytes, "image/jpeg")),
        ("files", ("test2.jpg", img2_bytes, "image/jpeg")),
    ]
    data = {"kind": "portfolio"}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    response = client.post(
        "/api/v1/media/artists/me/portfolio",
        files=files,
        data=data,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    
    # Verify portfolio images were created
    portfolio_images = db_session.query(PortfolioImage).filter(PortfolioImage.user_id == test_user.id).all()
    assert len(portfolio_images) == 2


def test_list_portfolio(client, db_session, test_user, test_session):
    """Test listing portfolio images."""
    # First upload some images
    img_bytes = create_test_image()
    files = [("files", ("test.jpg", img_bytes, "image/jpeg"))]
    data = {"kind": "portfolio"}
    headers = {"Authorization": f"Bearer {test_session}"}
    
    client.post("/api/v1/media/artists/me/portfolio", files=files, data=data, headers=headers)
    
    # Now list them
    response = client.get("/api/v1/media/artists/me/portfolio", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_delete_portfolio_image(client, db_session, test_user, test_session):
    """Test deleting a portfolio image."""
    # Create a portfolio image
    portfolio_image = PortfolioImage(
        user_id=test_user.id,
        kind="portfolio",
        url="/media/test.jpg",
        width=1200,
        height=1200,
        mime_type="image/jpeg",
    )
    db_session.add(portfolio_image)
    db_session.commit()
    db_session.refresh(portfolio_image)
    
    # Delete it
    headers = {"Authorization": f"Bearer {test_session}"}
    response = client.delete(
        f"/api/v1/media/portfolio/{portfolio_image.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify it was deleted
    deleted = db_session.query(PortfolioImage).filter(PortfolioImage.id == portfolio_image.id).first()
    assert deleted is None
