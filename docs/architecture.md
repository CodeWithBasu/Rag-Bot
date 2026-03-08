# Architecture Overview

## 1. High-Level System Architecture

```
┌──────────────────────┐         ┌──────────────────────────────┐
│   React Frontend     │  HTTP   │   FastAPI Backend             │
│   (Vite, Port 5173)  │◄──────►│   (Uvicorn, Port 8000)       │
│                      │  REST   │                              │
│  • Login / Register  │         │  • Auth (JWT + bcrypt)       │
│  • Upload Documents  │         │  • Document Processing       │
│  • AI Chat Interface │         │  • Vector Store Integration  │
│                      │         │  • RAG Engine (LangChain)    │
└──────────────────────┘         └──────┬──────────┬────────────┘
                                        │          │
                                        │          │
                               ┌────────▼──┐  ┌───▼──────────────┐
                               │  SQLite   │  │  Pinecone Cloud  │
                               │  (Local)  │  │  (Vector DB)     │
                               │           │  │                  │
                               │ • Users   │  │ • Document       │
                               │ • Docs    │  │   Embeddings     │
                               │   metadata│  │ • User-scoped    │
                               └───────────┘  └────────┬─────────┘
                                                       │
                                              ┌────────▼─────────┐
                                              │  Groq / HuggingFace│
                                              │  APIs            │
                                              │                  │
                                              │ • Embeddings     │
                                              │   (all-MiniLM-   │
                                              │    L6-v2)        │
                                              │ • LLM Chat       │
                                              │   (llama3-8b-    │
                                              │    8192)         │
                                              └──────────────────┘
```

## 2. Document Ingestion Flow

When a user uploads a document, the following sequence executes:

1. **Upload**: Frontend sends the raw file (PDF, DOCX, TXT) via multipart/form-data to `/documents/upload`.
2. **Auth Check**: Backend verifies the JWT token and identifies the user.
3. **Text Extraction**: Raw text is extracted using the appropriate library:
   - `.pdf` → `PyPDF` (reads all pages)
   - `.docx` → `python-docx` (reads all paragraphs)
   - `.txt` → Direct UTF-8 decode
4. **Chunking**: Text is split into ~1000 character chunks with 200 character overlap using `RecursiveCharacterTextSplitter`.
5. **Embedding**: Each chunk is converted to a 384-dimensional vector using `all-MiniLM-L6-v2`.
6. **Vector Storage**: Vectors + metadata (`user_id`, `filename`, `chunk_index`) are upserted to **Pinecone** index `rag-bot-index-hf`.
7. **Database Record**: Document metadata (filename, timestamp) is saved to SQLite.
8. **File Backup**: A copy of the original file is saved to `backend/uploads/`.

## 3. Query & Retrieval Flow (RAG Process)

1. **User Input**: User submits a natural language question via the Chat UI.
2. **Query Embedding**: The question is converted to the same 384-dimensional vector.
3. **Similarity Search**: Pinecone finds the top 5 most relevant text chunks.
   - **Critical**: A metadata filter `{"user_id": current_user.id}` ensures users only retrieve **their own** documents.
4. **Context Assembly**: Retrieved chunks are combined into a Context Window.
5. **LLM Generation**: The context + question are sent to `llama3-8b-8192` with a strict system prompt:
   > "Answer **only** from the provided context. If the answer isn't in the documents, say so."
6. **Response**: The AI answer + source filenames are returned to the user.

## 4. Key Design Decisions

| Decision                              | Rationale                                                            |
| ------------------------------------- | -------------------------------------------------------------------- |
| **Pinecone over local vector stores** | Cloud-hosted, no local memory constraints, serverless scaling        |
| **User-scoped metadata filtering**    | Absolute data isolation between users without separate indexes       |
| **all-MiniLM-L6-v2 (384-dim)**        | Fast, open-source local embedding model with good retrieval accuracy |
| **llama3-8b-8192 (via Groq)**         | Extremely fast, capable, and generous free-tier limits               |
| **LangChain orchestration**           | Standardized RAG pipeline with retriever + chain pattern             |
| **JWT authentication**                | Stateless, scalable, industry-standard token auth                    |
