from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import os
from fastapi.middleware.cors import CORSMiddleware

import models
import schemas
import auth
import document_processor
import vector_store
import rag_engine
from database import engine, get_db

# Create the database tables
models.Base.metadata.create_all(bind=engine)

os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="RAG Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite's default dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/documents/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    valid_extensions = (".pdf", ".docx", ".txt")
    if not file.filename.endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are supported.")

    # 1. Extract text from the file
    try:
        extracted_text = await document_processor.extract_text_from_upload(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    # 2. Vectorize and store 'extracted_text' in Pinecone in the background!
    # By shifting this to a BackgroundTask, a large 100-page PDF will return to the UI instantly
    # while the server processes the vectors seamlessly behind the scenes.
    if not os.getenv("PINECONE_API_KEY"):
         raise HTTPException(status_code=500, detail="Pinecone API Key is missing in your .env file.")
         
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")):
         raise HTTPException(status_code=500, detail="An LLM API Key (Groq, OpenAI, or Gemini) is missing in your .env file.")

    try:
        if extracted_text and extracted_text.strip():
            background_tasks.add_task(
                vector_store.process_and_store_text,
                text=extracted_text, 
                user_id=current_user.id, 
                filename=file.filename
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue vectorization: {str(e)}")

    # 3. Save file to disk
    file_location = f"uploads/{current_user.id}_{file.filename}"
    
    # We need to reset the cursor on the file since it was read in `extract_text_from_upload`
    # However, `extract_text_from_upload` read all bytes, so we can't easily read again unless we seek.
    # We can just rely on the temporary save we already did, or re-save. For now, since it was a temp file, 
    # we can modify `extract_text_from_upload` later to return bytes, or `seek(0)`.
    await file.seek(0)
    
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    # 3. Save to database
    db_document = models.Document(
        user_id=current_user.id,
        filename=file.filename,
        upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return db_document

@app.get("/documents", response_model=list[schemas.DocumentResponse])
def get_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(models.Document).filter(models.Document.user_id == current_user.id).all()
    return documents


@app.post("/chat", response_model=schemas.ChatResponse)
def chat_with_documents(
    query: schemas.ChatQuery,
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        response = rag_engine.generate_rag_response(
            query=query.query, 
            user_id=current_user.id
        )
        return {"answer": response["answer"], "sources": response["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@app.get("/")
def read_root():
    return {"Hello": "Welcome to RAG Bot API"}


