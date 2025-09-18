"""
Search Similar Tool MCP Server

An MCP server that provides search functionality for finding similar translation pairs.
This tool can be used with any MCP-compatible client.

Run with:
    uv run server search_similar_tool stdio
"""

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
from mcp.server.fastmcp import FastMCP

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

# Create MCP server
mcp = FastMCP("SearchSimilarTool")

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

# MCP Tools
@mcp.tool()
def get_top_k(user_input: str, target_language: str, top_k: int = 5) -> int:
    """Return the top_k parameter for search configuration"""
    return top_k

@mcp.tool()
def get_user_input(user_input: str, target_language: str, top_k: int = 5) -> str:
    """Return the user_input parameter"""
    return user_input

@mcp.tool()
def get_target_language(user_input: str, target_language: str, top_k: int = 5) -> str:
    """Return the target_language parameter"""
    return target_language

@mcp.tool()
def search_similar_pairs(user_input: str, target_language: str, top_k: int = 5) -> Dict[str, Any]:
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

# Health check tool
@mcp.tool()
def health_check() -> Dict[str, str]:
    """Health check for the search service"""
    return {"status": "healthy", "service": "search_similar_tool"}

# MCP Resources
@mcp.resource("translation://{pair_id}")
def get_translation_pair(pair_id: str) -> str:
    """Get a specific translation pair by ID"""
    try:
        db = SessionLocal()
        try:
            pair = db.query(TransAgent).filter(TransAgent.id == int(pair_id)).first()
            if not pair:
                return f"Translation pair with ID {pair_id} not found"
            
            return f"""Translation Pair #{pair.id}
GL Number: {pair.gl_number or 'N/A'}
Row Number: {pair.row_number or 'N/A'}
Version: {pair.version or 'N/A'}
Effective Date: {pair.effective_date or 'N/A'}

English Text: {pair.english_text}
Chinese Text: {pair.chinese_text}

Created At: {pair.created_at or 'N/A'}"""
        finally:
            db.close()
    except Exception as e:
        return f"Error retrieving translation pair: {str(e)}"

@mcp.resource("search://results/{query}")
def get_search_results(query: str) -> str:
    """Get formatted search results for a query"""
    try:
        # Use default search parameters
        result = search_similar_pairs(query, "chinese", 5)
        
        if "error" in result:
            return f"Search Error: {result['error']}"
        
        output = f"Search Results for: '{query}'\n"
        output += f"Query Language: {result['query_language']}\n"
        output += f"Target Language: {result['target_language']}\n"
        output += f"Total Found: {result['total_found']}\n\n"
        
        for i, pair in enumerate(result['pairs'], 1):
            output += f"{i}. Translation Pair #{pair['id']}\n"
            output += f"   English: {pair['english_text']}\n"
            output += f"   Chinese: {pair['chinese_text']}\n"
            output += f"   GL Number: {pair['gl_number'] or 'N/A'}\n\n"
        
        return output
    except Exception as e:
        return f"Error performing search: {str(e)}"

# MCP Prompts
@mcp.prompt()
def search_translation_prompt(text: str, target_language: str = "chinese", style: str = "detailed") -> str:
    """Generate a search prompt for finding similar translation pairs"""
    styles = {
        "detailed": "Please analyze the following text and search for similar translation pairs. Provide detailed explanations of the matches and their relevance.",
        "simple": "Find similar translation pairs for the given text.",
        "context": "Search for translation pairs and explain how they can be used in similar contexts."
    }
    
    prompt_style = styles.get(style, styles["detailed"])
    
    return f"""{prompt_style}

Text to search: "{text}"
Target language: {target_language}

Use the search_similar_pairs tool to find relevant translation pairs, then analyze the results and explain:
1. Why these pairs are similar to the input text
2. The context in which these translations would be appropriate
3. Any patterns you notice in the translation style
4. Suggestions for how to use these translations effectively
"""

@mcp.prompt()
def analyze_translation_quality(english_text: str, chinese_text: str) -> str:
    """Generate a prompt to analyze translation quality between English and Chinese text"""
    return f"""Please analyze the quality and accuracy of this translation pair:

English: "{english_text}"
Chinese: "{chinese_text}"

Consider the following aspects:
1. Accuracy: Is the meaning preserved?
2. Fluency: Does the translation sound natural?
3. Cultural appropriateness: Are cultural nuances handled well?
4. Terminology consistency: Are technical terms translated appropriately?
5. Style: Does the translation maintain the appropriate tone and style?

Provide a detailed analysis and suggest any improvements if needed.
"""

@mcp.prompt()
def suggest_search_terms(domain: str = "general", language: str = "english") -> str:
    """Generate suggestions for effective search terms in translation databases"""
    return f"""Generate effective search terms for finding translation pairs in the {domain} domain.

Language: {language}
Domain: {domain}

Please suggest:
1. Key phrases commonly used in {domain} contexts
2. Technical terminology specific to {domain}
3. Common sentence patterns for {language} in {domain} contexts
4. Alternative ways to express the same concepts

Format your suggestions as a list of search terms that would be effective with the search_similar_pairs tool.
"""

# Information tool
@mcp.tool()
def get_service_info() -> Dict[str, Any]:
    """Get information about the search service and available tools"""
    return {
        "service": "Search Similar Tool MCP Server",
        "version": "1.0.0",
        "tools": {
            "get_top_k": "Returns the top_k parameter for search configuration",
            "get_user_input": "Returns the user_input parameter",
            "get_target_language": "Returns the target_language parameter",
            "search_similar_pairs": "Finds top-k closest translation pairs",
            "health_check": "Health check for the service"
        }
    }

if __name__ == "__main__":
    # For MCP, the server is typically run via: uv run server search_similar_tool stdio
    # But we can also provide a way to test it directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Simple test mode
        result = search_similar_pairs("hello world", "chinese", 3)
        print("Test result:", result)
    else:
        print("This is an MCP server. Run with: uv run server search_similar_tool stdio")
        print("Or test with: python search_similar_tool.py test")
