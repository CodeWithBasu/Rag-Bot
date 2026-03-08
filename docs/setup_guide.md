# Setup & Troubleshooting Guide

## Prerequisites

| Tool        | Minimum Version  | Check Command      |
| ----------- | ---------------- | ------------------ |
| **Python**  | 3.10+            | `python --version` |
| **Node.js** | 20.19+ or 22.12+ | `node --version`   |
| **npm**     | 8+               | `npm --version`    |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/rag_bot.git
cd rag_bot
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file inside the `backend/` folder:

```env
GROQ_API_KEY="your-groq-api-key"
PINECONE_API_KEY="your-pinecone-api-key"
SECRET_KEY="any-random-secret-string-for-jwt"
```

**How to get API keys:**

- **Groq**: Go to [Groq Console](https://console.groq.com/keys) → Create API Key
- **Pinecone**: Go to [Pinecone Console](https://app.pinecone.io) → API Keys

### 4. Start the Backend

```bash
python -m uvicorn main:app --reload
```

✅ You should see: `Application startup complete.`

### 5. Frontend Setup (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

✅ You should see: `VITE ready` with `http://localhost:5173/`

### 6. Open the App

Go to **http://localhost:5173** in your browser!

---

## Troubleshooting

### ❌ "429 Quota Exceeded" Error

**What it means**: Your Groq API free-tier daily limit has been reached.

**Solution**: Wait for the quota to reset. Or consider using OpenAI if needed.

### ❌ "ERR_CONNECTION_REFUSED" in Browser

**What it means**: The backend server is not running.

**Solution**: Make sure both terminal commands are running:

- Backend: `python -m uvicorn main:app --reload` (in `backend/`)
- Frontend: `npm run dev` (in `frontend/`)

### ❌ "Vite requires Node.js 20.19+ or 22.12+"

**What it means**: Your Node.js version is too old for the installed Vite.

**Solution**: Either:

- Update Node.js from [nodejs.org](https://nodejs.org)
- Or downgrade Vite: `npm install vite@6.2.0`

### ❌ "Failed to vectorize document"

**What it means**: The embedding API call failed (usually quota or network issue).

**Solution**: Check the backend terminal for the specific error. If it's a 429, wait for quota reset. If it's a different error, verify your `GROQ_API_KEY` in `.env`.

### ❌ Import Errors on Backend Startup

**What it means**: Python package versions are incompatible.

**Solution**: Reinstall from the locked requirements:

```bash
pip install -r requirements.txt
```

### ❌ bcrypt / passlib errors during registration

**What it means**: `bcrypt` version 5.x is incompatible with `passlib`.

**Solution**: Downgrade bcrypt:

```bash
pip install bcrypt==4.0.1
```

---

## Supported File Types

| Format     | Extension | Processing Library | Notes                        |
| ---------- | --------- | ------------------ | ---------------------------- |
| PDF        | `.pdf`    | PyPDF              | Extracts text from all pages |
| Word       | `.docx`   | python-docx        | Extracts all paragraph text  |
| Plain Text | `.txt`    | Built-in Python    | Direct UTF-8 decode          |

---

## Key Configuration

| Setting           | File              | Current Value               |
| ----------------- | ----------------- | --------------------------- |
| Embedding Model   | `vector_store.py` | `all-MiniLM-L6-v2`          |
| LLM Model         | `rag_engine.py`   | `llama3-8b-8192`            |
| Vector Dimensions | `vector_store.py` | `384`                       |
| Pinecone Index    | `vector_store.py` | `rag-bot-index-hf`          |
| Chunk Size        | `vector_store.py` | `1000` chars, `200` overlap |
| Top-K Results     | `rag_engine.py`   | `5`                         |
| JWT Expiry        | `auth.py`         | `30` minutes                |
