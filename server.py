"""
Search Similar Tool MCP Server

An MCP server that provides search functionality for finding similar translation pairs.
This tool can be used with any MCP-compatible client.

Run with:
    python server.py
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import truststore

# Inject truststore into SSL
truststore.inject_into_ssl()

# Load environment variables
load_dotenv()

# Database setup
Base = declarative_base()

class TransAgent(Base):
    """Database model for translation pairs with embeddings"""
    __tablename__ = 'trans_agent'
    
    id = Column(Integer, primary_key=True, index=True)
    gl_number = Column(String, nullable=True)
    row_number = Column(String, nullable=True)
    version = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)
    english_text = Column(Text, nullable=False)
    chinese_text = Column(Text, nullable=False)
    english_embedding = Column(Vector(1024), nullable=True)  # Adjust dimensions as needed
    chinese_embedding = Column(Vector(1024), nullable=True)  # Adjust dimensions as needed

# Database connection from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class LocalVLLMEmbeddings:
    """Local VLLM embeddings client"""
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

# Initialize embeddings from environment variables
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

if not EMBEDDING_ENDPOINT or not EMBEDDING_MODEL:
    raise ValueError("EMBEDDING_ENDPOINT and EMBEDDING_MODEL environment variables are required")

embeddings = LocalVLLMEmbeddings(
    endpoint=EMBEDDING_ENDPOINT,
    model=EMBEDDING_MODEL
)

def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese or English"""
    zh_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    return "zh" if zh_chars > en_chars else "en"

# Initialize FastMCP server
mcp = FastMCP("search-similar-tool")

# Helper function for making database requests with proper error handling
async def make_database_request(query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    """Make a database request with proper error handling."""
    db = SessionLocal()
    try:
        # Query using embedding similarity (cosine distance operator <=>)
        retrieved = (
            db.query(TransAgent)
            .order_by(TransAgent.english_embedding.op('<=>')(query_embedding))
            .limit(top_k)
            .all()
        )
        
        # Convert results to dictionary format
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
                    "created_at": str(getattr(row, 'created_at', None)) if hasattr(row, 'created_at') else None
                }
            }
            pairs.append(pair)
        
        return pairs
        
    finally:
        db.close()

def format_search_result(pair: Dict[str, Any]) -> str:
    """Format a translation pair into a readable string."""
    return f"""
Translation Pair #{pair['id']}:
GL Number: {pair.get('gl_number', 'N/A')}
Row Number: {pair.get('row_number', 'N/A')}
Version: {pair.get('version', 'N/A')}
Effective Date: {pair.get('effective_date', 'N/A')}

English Text: {pair['english_text']}
Chinese Text: {pair['chinese_text']}

Created At: {pair['metadata'].get('created_at', 'N/A')}
"""

# MCP Tools
@mcp.tool()
async def search_similar_pairs(user_input: str, target_language: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Find top-k closest translation pairs based on embedding similarity.
    
    Args:
        user_input: The text to search for similar translations
        target_language: Target language ('chinese' or 'english')
        top_k: Number of similar pairs to retrieve (1-20)
    
    Returns:
        Dictionary containing pairs, total_found, query_language, and target_language
    """
    try:
        # Validate top_k
        if not 1 <= top_k <= 20:
            top_k = min(max(top_k, 1), 20)
        
        # Detect the language of the input
        detected_lang = detect_language(user_input)
        
        # Generate embedding for the user input
        query_embedding = embeddings.embed_query(user_input)
        
        # Search database for similar pairs
        pairs = await make_database_request(query_embedding, top_k)
        
        return {
            "pairs": pairs,
            "total_found": len(pairs),
            "query_language": detected_lang,
            "target_language": target_language
        }
        
    except Exception as e:
        return {
            "error": f"Error searching for similar pairs: {str(e)}",
            "pairs": [],
            "total_found": 0,
            "query_language": "unknown",
            "target_language": target_language
        }

@mcp.tool()
async def get_translation_pair(pair_id: int) -> Dict[str, Any]:
    """
    Get a specific translation pair by ID.
    
    Args:
        pair_id: The ID of the translation pair to retrieve
    
    Returns:
        Dictionary containing the translation pair details
    """
    try:
        db = SessionLocal()
        try:
            pair = db.query(TransAgent).filter(TransAgent.id == pair_id).first()
            if not pair:
                return {"error": f"Translation pair with ID {pair_id} not found"}
            
            return {
                "id": pair.id,
                "gl_number": pair.gl_number,
                "row_number": pair.row_number,
                "version": pair.version,
                "effective_date": pair.effective_date,
                "english_text": pair.english_text,
                "chinese_text": pair.chinese_text,
                "created_at": str(getattr(pair, 'created_at', None)) if hasattr(pair, 'created_at') else None
            }
        finally:
            db.close()
    except Exception as e:
        return {"error": f"Error retrieving translation pair: {str(e)}"}

@mcp.tool()
def health_check() -> Dict[str, str]:
    """Health check for the search service"""
    try:
        # Test database connection
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "service": "search_similar_tool", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "search_similar_tool", "error": str(e)}

@mcp.tool()
def get_service_info() -> Dict[str, Any]:
    """Get information about the search service and available tools"""
    return {
        "service": "Search Similar Tool MCP Server",
        "version": "1.0.0",
        "description": "Provides search functionality for finding similar translation pairs using embeddings",
        "tools": {
            "search_similar_pairs": "Finds top-k closest translation pairs based on embedding similarity",
            "get_translation_pair": "Retrieves a specific translation pair by ID",
            "health_check": "Health check for the service and database connection",
            "get_service_info": "Returns information about the service and available tools"
        },
        "database": {
            "url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "configured",
            "table": "trans_agent"
        }
    }

# MCP Resources
@mcp.resource("translation://{pair_id}")
def get_translation_resource(pair_id: str) -> str:
    """Get a specific translation pair by ID as a formatted resource"""
    try:
        db = SessionLocal()
        try:
            pair = db.query(TransAgent).filter(TransAgent.id == int(pair_id)).first()
            if not pair:
                return f"Translation pair with ID {pair_id} not found"
            
            return format_search_result({
                "id": pair.id,
                "gl_number": pair.gl_number,
                "row_number": pair.row_number,
                "version": pair.version,
                "effective_date": pair.effective_date,
                "english_text": pair.english_text,
                "chinese_text": pair.chinese_text,
                "metadata": {
                    "created_at": str(getattr(pair, 'created_at', None)) if hasattr(pair, 'created_at') else None
                }
            })
        finally:
            db.close()
    except Exception as e:
        return f"Error retrieving translation pair: {str(e)}"

@mcp.resource("search://results/{query}")
def get_search_results_resource(query: str) -> str:
    """Get formatted search results for a query as a resource"""
    try:
        # Use default search parameters - Note: this should be async but resources don't support async yet
        # We'll need to use a synchronous version for now
        detected_lang = detect_language(query)
        query_embedding = embeddings.embed_query(query)
        
        db = SessionLocal()
        try:
            retrieved = (
                db.query(TransAgent)
                .order_by(TransAgent.english_embedding.op('<=>')(query_embedding))
                .limit(5)
                .all()
            )
            
            if not retrieved:
                return f"No search results found for: '{query}'"
            
            output = f"Search Results for: '{query}'\n"
            output += f"Query Language: {detected_lang}\n"
            output += f"Total Found: {len(retrieved)}\n\n"
            
            for i, row in enumerate(retrieved, 1):
                output += f"{i}. Translation Pair #{row.id}\n"
                output += f"   English: {row.english_text}\n"
                output += f"   Chinese: {row.chinese_text}\n"
                output += f"   GL Number: {row.gl_number or 'N/A'}\n\n"
            
            return output
        finally:
            db.close()
            
    except Exception as e:
        return f"Error performing search: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')