@echo off
echo ==========================================
echo 🤖 Starting RAG Bot...
echo ==========================================

start cmd /k "echo Starting Backend... && cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload"
start cmd /k "echo Starting Frontend... && cd frontend && npm run dev"

echo 🌐 Backend: http://localhost:8000
echo 🎨 Frontend: http://localhost:5173
echo ==========================================
echo Close the terminals to stop the app.
echo ==========================================
