# Security

## 1. Authentication — JWT Tokens

| Property             | Value                               |
| -------------------- | ----------------------------------- |
| **Protocol**         | OAuth2 Password Flow                |
| **Token Type**       | JSON Web Token (JWT)                |
| **Algorithm**        | HS256 (symmetric signing)           |
| **Expiry**           | 30 minutes                          |
| **Library**          | `python-jose` for encoding/decoding |
| **Password Hashing** | `passlib` with `bcrypt` scheme      |

### Flow

1. User sends credentials to `POST /auth/login`
2. Backend verifies password hash using `passlib.bcrypt.verify()`
3. If valid, a JWT is created with payload `{"sub": username, "exp": timestamp}`
4. Token is returned to the frontend and stored in `localStorage`
5. Every subsequent API call includes `Authorization: Bearer <token>` header
6. Backend decodes token via `Depends(get_current_user)` on every protected endpoint

## 2. Data Isolation — Multi-Tenant Security

This is the most critical security feature. Even though all users share the same Pinecone index, **no user can ever access another user's documents**.

### How it works:

**On Upload** — Every document chunk is tagged with the uploader's ID:

```python
metadatas = [
    {"user_id": current_user.id, "filename": file.filename, "chunk_index": i}
    for i in range(len(chunks))
]
```

**On Chat** — Every search query is filtered by the current user's ID:

```python
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"user_id": user_id}  # Only this user's chunks
    }
)
```

**Result**: Pinecone physically excludes all vectors that don't belong to the authenticated user. It is architecturally impossible for User A to retrieve User B's document content.

## 3. Secret Management

| Secret             | Storage                           | Notes                        |
| ------------------ | --------------------------------- | ---------------------------- |
| `GROQ_API_KEY`     | `.env` file                       | Never committed to Git       |
| `PINECONE_API_KEY` | `.env` file                       | Never committed to Git       |
| `SECRET_KEY`       | `.env` file                       | Used for JWT signing         |
| User passwords     | SQLite (`hashed_password` column) | bcrypt hash, never plaintext |

### .gitignore Protection

The `.gitignore` file explicitly excludes:

```
.env
.env.*
*.db
```

This ensures no secrets or local database data are ever pushed to GitHub.

## 4. Frontend Auth Guards

- The React Router redirects unauthenticated users to `/login`
- Protected routes check for `token` in state before rendering
- Logout clears `localStorage` and resets the token state
- No sensitive data (passwords, API keys) is ever exposed to the frontend
