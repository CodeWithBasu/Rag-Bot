import os
import time
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# --- Rate Limit Configuration ---
BATCH_SIZE = 200          # Maximize batch size (Pinecone limit is 1000) to decrease network latency
DELAY_BETWEEN_BATCHES = 0 # Reduced delay for local inference speed
MAX_RETRIES = 5           # Max retries on rate-limit (429) errors
INITIAL_BACKOFF = 2       # Initial backoff delay in seconds

# --- Global Caches to Speed up Request Times ---
_embeddings_instance = None
_index_name = None
_dimension = None
_vectorstore_instance = None

def get_embedding_model_and_index():
    global _embeddings_instance, _index_name, _dimension
    if _embeddings_instance is not None:
        return _embeddings_instance, _index_name, _dimension

    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if openai_api_key:
        from langchain_openai import OpenAIEmbeddings
        _embeddings_instance = OpenAIEmbeddings(api_key=openai_api_key)
        _index_name, _dimension = "rag-bot-index-openai", 1536
    elif groq_api_key:
        from langchain_huggingface import HuggingFaceEmbeddings
        # Uses a local embedding model, cached once in memory
        _embeddings_instance = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _index_name, _dimension = "rag-bot-index-hf", 384
    elif gemini_api_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        _embeddings_instance = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=gemini_api_key)
        _index_name, _dimension = "rag-bot-index-v3", 3072
    else:
        raise ValueError("Missing API Keys in .env file. Provide OPENAI_API_KEY, GROQ_API_KEY, or GEMINI_API_KEY.")
    
    return _embeddings_instance, _index_name, _dimension


def get_vector_store():
    global _vectorstore_instance
    if _vectorstore_instance is not None:
        return _vectorstore_instance

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("Missing PINECONE_API_KEY in .env file.")

    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)

    # Set up Embeddings and Index dynamically
    embeddings, index_name, dimension = get_embedding_model_and_index()
    
    # Check if index exists, if not, create it
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    _vectorstore_instance = PineconeVectorStore.from_existing_index(index_name, embeddings)
    return _vectorstore_instance


def _add_texts_with_retry(vectorstore, texts: list, metadatas: list):
    """Add a small batch of texts to Pinecone with retry logic for rate limits."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            vectorstore.add_texts(texts=texts, metadatas=metadatas)
            return  # Success — exit
        except Exception as e:
            error_msg = str(e)
            # Check if it's a rate-limit error (429)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(
                    f"Rate limit hit (attempt {attempt}/{MAX_RETRIES}). "
                    f"Waiting {backoff}s before retrying..."
                )
                time.sleep(backoff)
            else:
                # Not a rate-limit error — re-raise immediately
                raise
    # If we exhausted all retries
    raise RuntimeError(
        f"Failed to embed text after {MAX_RETRIES} retries due to API rate limits. "
        "Please wait a few minutes and try again, or upgrade your API plan."
    )


def process_and_store_text(text: str, user_id: int, filename: str):
    """Chunks text and uploads it to Pinecone with user_id metadata."""
    if not text.strip():
        return
        
    # 1. Chunk the text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    
    logger.info(f"Processing '{filename}': {len(chunks)} chunks (batch size: {BATCH_SIZE})")
    
    # 2. Add metadata
    # We include user_id so users can only search their OWN documents!
    metadatas = [{"user_id": user_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))]
    
    # 3. Store in Pinecone — in small batches to respect rate limits
    vectorstore = get_vector_store()
    
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch_texts = chunks[i : i + BATCH_SIZE]
        batch_metas = metadatas[i : i + BATCH_SIZE]
        
        logger.info(f"  Embedding batch {batch_num}/{total_batches} ({len(batch_texts)} chunks)...")
        _add_texts_with_retry(vectorstore, batch_texts, batch_metas)
        
        # Pause between batches to stay under rate limits
        if i + BATCH_SIZE < len(chunks) and DELAY_BETWEEN_BATCHES > 0:
            time.sleep(DELAY_BETWEEN_BATCHES)

