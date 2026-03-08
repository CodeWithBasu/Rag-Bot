# Database Schema

## 1. Local SQLite Database

The application uses SQLite via SQLAlchemy ORM. The database file `ragbot.db` is auto-created on first server startup.

### Users Table

```sql
CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR UNIQUE NOT NULL,
    email    VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL
);
```

| Column            | Type            | Description                                                        |
| ----------------- | --------------- | ------------------------------------------------------------------ |
| `id`              | Integer (PK)    | Auto-incrementing user ID. Used as `user_id` in Pinecone metadata. |
| `username`        | String (Unique) | Login identifier. Must be unique.                                  |
| `email`           | String (Unique) | Email address. Must be unique.                                     |
| `hashed_password` | String          | bcrypt-hashed password. Never stored in plaintext.                 |

### Documents Table

```sql
CREATE TABLE documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    filename    VARCHAR NOT NULL,
    upload_date VARCHAR NOT NULL
);
```

| Column        | Type         | Description                                                     |
| ------------- | ------------ | --------------------------------------------------------------- |
| `id`          | Integer (PK) | Auto-incrementing document ID.                                  |
| `user_id`     | Integer      | References `users.id`. Associates document with uploading user. |
| `filename`    | String       | Original filename preserved as uploaded.                        |
| `upload_date` | String       | Timestamp in `YYYY-MM-DD HH:MM:SS` format.                      |

---

## 2. Pinecone Vector Database

**Index Name**: `rag-bot-index-hf`  
**Dimension**: `384` (matches `all-MiniLM-L6-v2` output)  
**Metric**: Cosine Similarity  
**Cloud**: AWS `us-east-1` (Serverless)

### Vector Record Structure

```json
{
    "id": "auto-generated-uuid",
    "values": [0.032, -0.015, 0.089, ...],  // 384 floats
    "metadata": {
        "text": "The actual text chunk from the document...",
        "user_id": 1,
        "filename": "company-policy.pdf",
        "chunk_index": 0
    }
}
```

### Metadata Fields

| Field         | Type    | Purpose                                                                   |
| ------------- | ------- | ------------------------------------------------------------------------- |
| `text`        | string  | The literal text chunk that was embedded. Returned as context to the LLM. |
| `user_id`     | integer | Links chunk to the user who uploaded it. **Critical for data isolation.** |
| `filename`    | string  | Original filename. Shown as "Source" in chat responses.                   |
| `chunk_index` | integer | Position of this chunk within the document.                               |

### How Data Isolation Works

When querying Pinecone, a metadata filter is always applied:

```python
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"user_id": current_user.id}  # ← This is the key
    }
)
```

This means **User A can never see, retrieve, or chat about User B's documents**, even if they upload identical files.
