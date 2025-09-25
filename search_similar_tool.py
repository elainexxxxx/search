"""
Search Similar Tool MCP Server

An MCP server that provides search functionality for finding similar translation pairs.
This tool can be called via MCP tools.

Tools:
- get_top_k: Returns the top_k parameter
- get_user_input: Returns the user_input parameter  
- get_target_language: Returns the target_language parameter
- get_pairs: Finds top-k closest retrieved_chunks based on embedding similarity
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv(override=True)

# Create MCP server
mcp = FastMCP("search-similar-tool-server")

# Database setup
Base = declarative_base()

class TransAgent(Base):
    __tablename__ = "trans_agent_train"
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

# Request/Response models
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

# MCP Tools
@mcp.tool()
async def get_top_k(user_input: str, target_language: str, top_k: int = 5) -> int:
    """Return the top_k parameter from the request."""
    return top_k

@mcp.tool()
async def get_user_input(user_input: str, target_language: str, top_k: int = 5) -> str:
    """Return the user_input parameter from the request."""
    return user_input

@mcp.tool()
async def get_target_language(user_input: str, target_language: str, top_k: int = 5) -> str:
    """Return the target_language parameter from the request."""
    return target_language

@mcp.tool()
async def get_pairs(user_input: str, target_language: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Find top-k closest retrieved_chunks based on embedding similarity.
    
    This function:
    1. Embeds the user_input text
    2. Searches the database for similar translation pairs
    3. Returns the most similar pairs based on cosine similarity
    """
    try:
        # Validate parameters
        if top_k < 1 or top_k > 20:
            top_k = min(max(top_k, 1), 20)
        
        # Detect the language of the input
        detected_lang = detect_language(user_input)
        
        # Generate embedding for the user input
        query_embedding = embeddings.embed_query(user_input)
        
        # Search database for similar pairs
        db = SessionLocal()
        try:
            # Query using embedding similarity (cosine distance operator <=>)
            retrieved = (
                db.query(TransAgent)
                .order_by(TransAgent.english_embedding.op('<=>')(query_embedding))
                .limit(top_k)
                .all()
            )
            
            # Convert results to response format
            pairs = []
            for row in retrieved:
                pair = {
                    "id": row.id,
                    "gl_number": row.gl_number,
                    "row_number": row.row_number,
                    "version": row.version,
                    "effective_date": row.effective_date,
                    "english_text": row.english_text,
                    "chinese_text": row.chinese_text,
                    "context": row.english_text,
                    "metadata": {
                        "created_at": str(row.created_at) if row.created_at else None
                    }
                }
                pairs.append(pair)
            
            return {
                "pairs": pairs,
                "total_found": len(pairs),
                "query_language": detected_lang,
                "target_language": target_language
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "error": f"Error searching for similar pairs: {str(e)}",
            "pairs": [],
            "total_found": 0,
            "query_language": "unknown",
            "target_language": target_language
        }

# Run MCP server
if __name__ == "__main__":
       asyncio.run(mcp.run(transport="http", host="0.0.0.0", port=8000))
