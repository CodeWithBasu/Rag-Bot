from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

import schemas
import auth
import document_processor
import vector_store
import rag_engine
from database import get_db

app = FastAPI(
    title="RAG Bot API (MongoDB Edition)",
    # Pass root_path to allow FastAPI to handle /api prefix correctly when proxied on Vercel
    root_path="/api" if os.getenv("VERCEL") else ""
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to format MongoDB document for response
def format_doc(doc):
    doc["id"] = str(doc["_id"])
    return doc

@app.post("/auth/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db = Depends(get_db)):
    # Check if user already exists
    existing_user = await db["users"].find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })
    
    if existing_user:
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password
    }
    
    result = await db["users"].insert_one(new_user)
    new_user["id"] = str(result.inserted_id)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = await db["users"].find_one({"username": form_data.username})
    
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(auth.get_current_user)):
    return current_user


@app.post("/documents/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(auth.get_current_user),
    db = Depends(get_db)
):
    valid_extensions = (".pdf", ".docx", ".txt")
    if not file.filename.endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are supported.")

    # 1. Extract text from the file
    try:
        extracted_text = await document_processor.extract_text_from_upload(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    # Check for API Keys
    if not os.getenv("PINECONE_API_KEY"):
         raise HTTPException(status_code=500, detail="Pinecone API Key is missing.")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")):
         raise HTTPException(status_code=500, detail="LLM API Key (Groq/OpenAI/Gemini) is missing.")

    # 2. Vectorize in the background
    try:
        if extracted_text and extracted_text.strip():
            background_tasks.add_task(
                vector_store.process_and_store_text,
                text=extracted_text, 
                user_id=current_user["id"], 
                filename=file.filename
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue vectorization: {str(e)}")

    # 3. Handle local file storage (Optional for Cloud deployment)
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{current_user['id']}_{file.filename}"
    await file.seek(0)
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    # 4. Save to MongoDB
    db_document = {
        "user_id": current_user["id"],
        "filename": file.filename,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    result = await db["documents"].insert_one(db_document)
    db_document["id"] = str(result.inserted_id)

    return db_document

@app.get("/documents", response_model=List[schemas.DocumentResponse])
async def get_documents(
    current_user: Dict[str, Any] = Depends(auth.get_current_user),
    db = Depends(get_db)
):
    cursor = db["documents"].find({"user_id": current_user["id"]})
    documents = []
    async for doc in cursor:
        documents.append(format_doc(doc))
    return documents


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_documents(
    query: schemas.ChatQuery,
    current_user: Dict[str, Any] = Depends(auth.get_current_user),
):
    try:
        response = rag_engine.generate_rag_response(
            query=query.query, 
            user_id=current_user["id"]
        )
        return {"answer": response["answer"], "sources": response["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")


@app.get("/")
async def read_root():
    return {"status": "online", "database": "mongodb", "engine": "rag-bot-v2"}
