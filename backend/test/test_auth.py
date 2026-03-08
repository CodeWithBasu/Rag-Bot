"""
Tests for the authentication system.

Covers:
- User registration (success + duplicate handling)
- User login (success + invalid credentials)
- JWT token validation & protected routes
- Password hashing
"""
import pytest
import auth


# ─── REGISTRATION TESTS ────────────────────────────────────────────────

class TestRegistration:
    
    def test_register_success(self, client):
        """A new user can register successfully."""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        # Password should NEVER be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Cannot register with an email that already exists."""
        response = client.post("/auth/register", json={
            "username": "differentuser",
            "email": "test@example.com",  # same email as test_user
            "password": "AnotherPass123"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Cannot register with a username that already exists."""
        response = client.post("/auth/register", json={
            "username": "testuser",  # same username as test_user
            "email": "different@example.com",
            "password": "AnotherPass123"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Registration fails with an invalid email format."""
        response = client.post("/auth/register", json={
            "username": "baduser",
            "email": "not-an-email",
            "password": "SecurePass123"
        })
        assert response.status_code == 422  # Pydantic validation error


# ─── LOGIN TESTS ───────────────────────────────────────────────────────

class TestLogin:

    def test_login_success(self, client, test_user):
        """A registered user can login and receive a JWT token."""
        response = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Login fails with incorrect password."""
        response = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": "WrongPassword!"
        })
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Login fails for a user that doesn't exist."""
        response = client.post("/auth/login", data={
            "username": "ghost",
            "password": "SomePass123"
        })
        assert response.status_code == 401


# ─── JWT & PROTECTED ROUTES ───────────────────────────────────────────

class TestJWTAuth:

    def test_get_current_user(self, client, auth_headers):
        """Authenticated user can access /users/me."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_access_protected_route_without_token(self, client):
        """Accessing a protected route without a token returns 401."""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_access_protected_route_with_invalid_token(self, client):
        """Accessing a protected route with an invalid token returns 401."""
        response = client.get("/users/me", headers={
            "Authorization": "Bearer totally-fake-token"
        })
        assert response.status_code == 401


# ─── PASSWORD HASHING TESTS ───────────────────────────────────────────

class TestPasswordHashing:

    def test_hash_and_verify(self):
        """Password hash can be verified with the original password."""
        password = "MySecretPass!123"
        hashed = auth.get_password_hash(password)
        
        assert hashed != password  # Not stored as plain text
        assert auth.verify_password(password, hashed) is True

    def test_different_passwords_different_hashes(self):
        """Two different passwords produce different hashes."""
        hash1 = auth.get_password_hash("Password1")
        hash2 = auth.get_password_hash("Password2")
        assert hash1 != hash2

    def test_wrong_password_fails_verification(self):
        """Wrong password fails verification."""
        hashed = auth.get_password_hash("CorrectPassword")
        assert auth.verify_password("WrongPassword", hashed) is False
