# API Reference

The FastAPI backend exposes a RESTful API at `http://127.0.0.1:8000`.

> **Interactive Docs**: Visit `http://127.0.0.1:8000/docs` for Swagger UI when the server is running.

---

## Authentication

### Register User

```
POST /auth/register
```

| Parameter  | Type   | Location    | Required |
| ---------- | ------ | ----------- | -------- |
| `username` | string | body (JSON) | ✅       |
| `email`    | string | body (JSON) | ✅       |
| `password` | string | body (JSON) | ✅       |

**Response** `200 OK`:

```json
{
  "id": 1,
  "username": "ankit",
  "email": "ankit@example.com"
}
```

**Errors**: `400` if email or username already exists.

---

### Login

```
POST /auth/login
```

| Parameter  | Type   | Location  | Required |
| ---------- | ------ | --------- | -------- |
| `username` | string | form-data | ✅       |
| `password` | string | form-data | ✅       |

**Response** `200 OK`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors**: `401` if credentials are incorrect.

---

### Get Current User

```
GET /users/me
Authorization: Bearer <token>
```

**Response** `200 OK`:

```json
{
  "id": 1,
  "username": "ankit",
  "email": "ankit@example.com"
}
```

---

## Documents

### Upload Document

```
POST /documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

| Parameter | Type | Location  | Required |
| --------- | ---- | --------- | -------- |
| `file`    | File | form-data | ✅       |

**Accepted formats**: `.pdf`, `.docx`, `.txt`

**What happens on upload**:

1. Text is extracted from the file
2. Text is chunked into ~1000 character segments
3. Each chunk is embedded using `all-MiniLM-L6-v2` (384 dimensions)
4. Vectors are stored in Pinecone with `user_id` metadata
5. File metadata is saved to SQLite
6. A backup copy is saved to `backend/uploads/`

**Response** `200 OK`:

```json
{
  "id": 1,
  "user_id": 1,
  "filename": "resume.pdf",
  "upload_date": "2026-02-28 23:00:00"
}
```

**Errors**: `400` for invalid file types, `500` for processing or API errors.

---

### List My Documents

```
GET /documents
Authorization: Bearer <token>
```

**Response** `200 OK`:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "filename": "resume.pdf",
    "upload_date": "2026-02-28 23:00:00"
  }
]
```

---

## Chat

### Ask a Question

```
POST /chat
Authorization: Bearer <token>
```

| Parameter | Type   | Location    | Required |
| --------- | ------ | ----------- | -------- |
| `query`   | string | body (JSON) | ✅       |

**What happens**:

1. Query is embedded using the same model
2. Pinecone retrieves top 5 most relevant chunks (filtered by `user_id`)
3. Chunks are assembled as context for the LLM
4. `llama3-8b-8192` generates an answer strictly from the context
5. Source filenames are extracted and returned

**Response** `200 OK`:

```json
{
  "answer": "Based on your documents, the capital of France is Paris...",
  "sources": ["geography.pdf", "notes.txt"]
}
```

**Errors**: `500` if API quota exceeded or processing fails.
