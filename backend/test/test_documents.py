"""
Tests for document upload and management.

Covers:
- Document upload (valid file types)
- Invalid file type rejection
- Document listing (user-scoped)
- Upload without authentication
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import io


# ─── DOCUMENT UPLOAD TESTS ─────────────────────────────────────────────

class TestDocumentUpload:

    @patch("main.vector_store.process_and_store_text")
    @patch("main.document_processor.extract_text_from_upload", new_callable=AsyncMock)
    def test_upload_txt_file(self, mock_extract, mock_vectorize, client, auth_headers):
        """Successfully upload a .txt file."""
        mock_extract.return_value = "This is sample document text for testing."
        mock_vectorize.return_value = None

        file_content = b"This is sample document text for testing."
        response = client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_doc.txt"
        assert "id" in data
        assert "user_id" in data
        assert "upload_date" in data
        
        # Verify the processing pipeline was called
        mock_extract.assert_called_once()
        mock_vectorize.assert_called_once()

    @patch("main.vector_store.process_and_store_text")
    @patch("main.document_processor.extract_text_from_upload", new_callable=AsyncMock)
    def test_upload_pdf_file(self, mock_extract, mock_vectorize, client, auth_headers):
        """Successfully upload a .pdf file."""
        mock_extract.return_value = "Extracted PDF text content."
        mock_vectorize.return_value = None

        response = client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 fake pdf"), "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.json()["filename"] == "report.pdf"

    @patch("main.vector_store.process_and_store_text")
    @patch("main.document_processor.extract_text_from_upload", new_callable=AsyncMock)
    def test_upload_docx_file(self, mock_extract, mock_vectorize, client, auth_headers):
        """Successfully upload a .docx file."""
        mock_extract.return_value = "Extracted Word document content."
        mock_vectorize.return_value = None

        response = client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("notes.docx", io.BytesIO(b"fake docx"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        
        assert response.status_code == 200
        assert response.json()["filename"] == "notes.docx"

    def test_upload_invalid_file_type(self, client, auth_headers):
        """Uploading an unsupported file type returns 400."""
        response = client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("image.png", io.BytesIO(b"fake image"), "image/png")}
        )
        
        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_upload_without_auth(self, client):
        """Uploading without authentication returns 401."""
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        )
        assert response.status_code == 401


# ─── DOCUMENT LISTING TESTS ────────────────────────────────────────────

class TestDocumentListing:

    def test_list_documents_empty(self, client, auth_headers):
        """New user has no documents."""
        response = client.get("/documents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @patch("main.vector_store.process_and_store_text")
    @patch("main.document_processor.extract_text_from_upload", new_callable=AsyncMock)
    def test_list_documents_after_upload(self, mock_extract, mock_vectorize, client, auth_headers):
        """After uploading a document, it appears in the list."""
        mock_extract.return_value = "Extracted text."
        mock_vectorize.return_value = None

        # Upload a doc
        client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        )

        # List documents
        response = client.get("/documents", headers=auth_headers)
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) == 1
        assert docs[0]["filename"] == "test.txt"

    def test_list_documents_without_auth(self, client):
        """Listing documents without authentication returns 401."""
        response = client.get("/documents")
        assert response.status_code == 401


# ─── DATA ISOLATION TESTS ──────────────────────────────────────────────

class TestDataIsolation:

    @patch("main.vector_store.process_and_store_text")
    @patch("main.document_processor.extract_text_from_upload", new_callable=AsyncMock)
    def test_users_cannot_see_each_others_documents(self, mock_extract, mock_vectorize, client):
        """User A's documents should not appear in User B's list."""
        mock_extract.return_value = "Extracted text."
        mock_vectorize.return_value = None

        # Register and login as User A
        client.post("/auth/register", json={
            "username": "user_a", "email": "a@test.com", "password": "PassA123"
        })
        login_a = client.post("/auth/login", data={"username": "user_a", "password": "PassA123"})
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        # Register and login as User B
        client.post("/auth/register", json={
            "username": "user_b", "email": "b@test.com", "password": "PassB123"
        })
        login_b = client.post("/auth/login", data={"username": "user_b", "password": "PassB123"})
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # User A uploads a document
        client.post(
            "/documents/upload", headers=headers_a,
            files={"file": ("secret_a.txt", io.BytesIO(b"User A's secret"), "text/plain")}
        )

        # User B should NOT see User A's document
        response = client.get("/documents", headers=headers_b)
        assert response.status_code == 200
        assert len(response.json()) == 0  # User B sees nothing
