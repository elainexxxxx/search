"""
Search Similar Tool Server

A FastAPI server that provides search functionality for finding similar translation pairs.
This tool can be called independently via HTTP API endpoints.

Endpoints:
- /get_top_k: Returns the top_k parameter
- /get_user_input: Returns the user_input parameter  
- /get_target_language: Returns the target_language parameter
- /get_pairs: Finds top-k closest retrieved_chunks based on embedding similarity
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Database setup
Base = declarative_base()

class TransAgent(Base):
    __tablename__ = "trans_agent"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gl_number = Column(String)
    row_number = Column(String)
    version = Column(String)
    effective_date = Column(String)
    english_text = Column(Text)
    chinese_text = Column(Text)
    english_embedding = Column(Vector(768))
    chinese_embedding = Column(Vector(768))
    created_at = Column(DateTime(timezone=True))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:Abc123@10.96.184.114:5431/ai_platform")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class LocalVLLMEmbeddings:
    def __init__(self, endpoint: str, model: str):
        self.endpoint = endpoint
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import requests
        payload = {"model": self.model, "input": texts}
        response = requests.post(self.endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
    
    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

# Initialize embeddings
embeddings = LocalVLLMEmbeddings(
    endpoint="http://10.96.184.114:8007/v1/embeddings",
    model="hosted_vllm/Dmeta"
)

def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese or English"""
    zh_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    return "zh" if zh_chars > en_chars else "en"

# FastAPI app
app = FastAPI(
    title="Search Similar Tool Server",
    description="Independent tool server for finding similar translation pairs",
    version="1.0.0"
)

# Request/Response models
class SearchRequest(BaseModel):
    user_input: str = Field(..., description="The text to search for similar translations")
    target_language: str = Field(..., description="Target language: 'chinese' or 'english'")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar pairs to retrieve")

class BasicResponse(BaseModel):
    value: Any = Field(..., description="The requested value")

class TranslationPair(BaseModel):
    id: int
    gl_number: Optional[str]
    row_number: Optional[str]
    version: Optional[str]
    effective_date: Optional[str]
    english_text: str
    chinese_text: str
    context: str
    metadata: Dict[str, Any]

class PairsResponse(BaseModel):
    pairs: List[TranslationPair]
    total_found: int
    query_language: str
    target_language: str

# API Endpoints
@app.post("/get_top_k", response_model=BasicResponse)
async def get_top_k(request: SearchRequest):
    """Return the top_k parameter from the request"""
    return BasicResponse(value=request.top_k)

@app.post("/get_user_input", response_model=BasicResponse)
async def get_user_input(request: SearchRequest):
    """Return the user_input parameter from the request"""
    return BasicResponse(value=request.user_input)

@app.post("/get_target_language", response_model=BasicResponse)
async def get_target_language(request: SearchRequest):
    """Return the target_language parameter from the request"""
    return BasicResponse(value=request.target_language)

@app.post("/get_pairs", response_model=PairsResponse)
async def get_pairs(request: SearchRequest):
    """
    Find top-k closest retrieved_chunks based on embedding similarity.
    
    This function:
    1. Embeds the user_input text
    2. Searches the database for similar translation pairs
    3. Returns the most similar pairs based on cosine similarity
    """
    try:
        # Detect the language of the input
        detected_lang = detect_language(request.user_input)
        
        # Generate embedding for the user input
        query_embedding = embeddings.embed_query(request.user_input)
        
        # Search database for similar pairs
        db = SessionLocal()
        try:
            # Query using embedding similarity (cosine distance operator <=>)
            retrieved = (
                db.query(TransAgent)
                .order_by(TransAgent.english_embedding.op('<=>')(query_embedding))
                .limit(request.top_k)
                .all()
            )
            
            # Convert results to response format
            pairs = []
            for row in retrieved:
                pair = TranslationPair(
                    id=row.id,
                    gl_number=row.gl_number,
                    row_number=row.row_number,
                    version=row.version,
                    effective_date=row.effective_date,
                    english_text=row.english_text,
                    chinese_text=row.chinese_text,
                    context=row.english_text,
                    metadata={
                        "created_at": str(row.created_at) if row.created_at else None
                    }
                )
                pairs.append(pair)
            
            return PairsResponse(
                pairs=pairs,
                total_found=len(pairs),
                query_language=detected_lang,
                target_language=request.target_language
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching for similar pairs: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "search_similar_tool"}

# Root endpoint with API information
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Search Similar Tool Server",
        "version": "1.0.0",
        "endpoints": {
            "get_top_k": "POST /get_top_k - Returns the top_k parameter",
            "get_user_input": "POST /get_user_input - Returns the user_input parameter",
            "get_target_language": "POST /get_target_language - Returns the target_language parameter",
            "get_pairs": "POST /get_pairs - Finds top-k closest translation pairs",
            "health": "GET /health - Health check",
            "docs": "GET /docs - API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
