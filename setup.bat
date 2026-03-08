@echo off
setlocal
echo ==================================================
echo 🤖 RAG Bot - Automated Setup Engine
echo ==================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+ and try again.
    pause
    exit /b
)

:: Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js and try again.
    pause
    exit /b
)

echo [1/4] 🔧 Initializing Backend...
cd backend
if not exist venv (
    echo   - Creating Virtual Environment...
    python -m venv venv
)
echo   - Installing Python Modules (This may take a moment)...
call venv\Scripts\activate
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt --quiet

if not exist .env (
    echo   - Generating .env template...
    echo GROQ_API_KEY="PASTE_KEY_HERE" > .env
    echo PINECONE_API_KEY="PASTE_KEY_HERE" >> .env
    echo SECRET_KEY="%RANDOM%%RANDOM%-%RANDOM%" >> .env
    echo ⚠️ Backend .env created. UPDATE YOUR API KEYS!
)
cd ..

echo [2/4] 📦 Initializing Frontend...
cd frontend
if not exist node_modules (
    echo   - Installing NPM Packages...
    call npm install --silent
)

if not exist .env (
    echo   - Configuring API endpoint...
    echo VITE_API_URL=http://127.0.0.1:8000 > .env
)
cd ..

echo ==================================================
echo ✅ SYSTEM READY!
echo ==================================================
echo 1. Open 'backend/.env' and add your API Keys.
echo 2. Run 'run.bat' to start the application.
echo ==================================================
pause
