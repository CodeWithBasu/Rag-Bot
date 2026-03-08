"""
Tests for the chat endpoint and RAG pipeline.

Covers:
- Chat endpoint (success + mocked RAG response)
- Chat without authentication
- Chat error handling
"""
import pytest
from unittest.mock import patch


# ─── CHAT ENDPOINT TESTS ──────────────────────────────────────────────

class TestChat:

    @patch("main.rag_engine.generate_rag_response")
    def test_chat_success(self, mock_rag, client, auth_headers):
        """A valid question returns an AI answer with sources."""
        mock_rag.return_value = {
            "answer": "The document mentions that the budget is $10 million.",
            "sources": ["quarterly_report.pdf"]
        }

        response = client.post(
            "/chat",
            headers=auth_headers,
            json={"query": "What is the budget?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "budget" in data["answer"].lower()
        assert "quarterly_report.pdf" in data["sources"]
        mock_rag.assert_called_once()

    @patch("main.rag_engine.generate_rag_response")
    def test_chat_no_relevant_docs(self, mock_rag, client, auth_headers):
        """When no relevant context is found, AI says so gracefully."""
        mock_rag.return_value = {
            "answer": "I cannot find the answer to this question in your uploaded documents.",
            "sources": []
        }

        response = client.post(
            "/chat",
            headers=auth_headers,
            json={"query": "What is quantum computing?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "cannot find" in data["answer"].lower()
        assert data["sources"] == []

    @patch("main.rag_engine.generate_rag_response")
    def test_chat_multiple_sources(self, mock_rag, client, auth_headers):
        """AI can cite multiple source documents."""
        mock_rag.return_value = {
            "answer": "Based on both documents, the revenue increased by 20%.",
            "sources": ["report_2024.pdf", "report_2025.pdf"]
        }

        response = client.post(
            "/chat",
            headers=auth_headers,
            json={"query": "How did revenue change?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2

    def test_chat_without_auth(self, client):
        """Chat without authentication returns 401."""
        response = client.post("/chat", json={"query": "Hello"})
        assert response.status_code == 401

    def test_chat_empty_query(self, client, auth_headers):
        """Sending an empty query should still work (no crash)."""
        with patch("main.rag_engine.generate_rag_response") as mock_rag:
            mock_rag.return_value = {
                "answer": "Please ask me a specific question about your documents.",
                "sources": []
            }
            response = client.post(
                "/chat",
                headers=auth_headers,
                json={"query": ""}
            )
            # Should not crash — either 200 or 422 depending on validation
            assert response.status_code in [200, 422]

    @patch("main.rag_engine.generate_rag_response")
    def test_chat_handles_rag_failure(self, mock_rag, client, auth_headers):
        """When RAG engine fails, a 500 error is returned gracefully."""
        mock_rag.side_effect = Exception("Pinecone connection timeout")

        response = client.post(
            "/chat",
            headers=auth_headers,
            json={"query": "What is in my documents?"}
        )

        assert response.status_code == 500
        assert "failed to generate response" in response.json()["detail"].lower()


# ─── ROOT ENDPOINT TEST ───────────────────────────────────────────────

class TestRootEndpoint:

    def test_root_returns_welcome(self, client):
        """The root / endpoint returns a welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome" in response.json()["Hello"] or "RAG Bot" in response.json()["Hello"]
