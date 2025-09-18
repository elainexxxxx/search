# Search Similar Tool MCP Server

This tool helps find the most relevant translation pairs from a database based on input text using the Model Context Protocol (MCP).

## Project Structure

```
search_pairs/
├── search_similar_tool.py      # Main MCP server application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image configuration
├── .env                       # Environment variables (create manually)
└── README.md                  # This documentation
```

## Features

- **MCP Protocol Support**: Fully compatible with Model Context Protocol
- **Language Detection**: Automatically detects whether input text is Chinese or English
- **Embedding Search**: Uses vector embeddings to find semantically similar translation pairs
- **Multiple Tools**: Provides various tools for different search and analysis tasks
- **Resources**: Access translation pairs through MCP resources
- **Prompts**: Built-in prompts for search guidance and analysis

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
DATABASE_URL=postgresql://admin:Abc123@10.96.184.114:5431/ai_platform
```

## Running the MCP Server

### Standard MCP Usage

Run the server using the MCP protocol:

```bash
# Using uv (recommended)
uv run server search_similar_tool stdio

# Or using python directly
python search_similar_tool.py
```

### Test Mode

Test the server functionality:

```bash
python search_similar_tool.py test
```

## MCP Tools

The server provides the following tools that can be called by MCP clients:

### 1. search_similar_pairs

Find top-k closest translation pairs based on embedding similarity.

**Parameters:**
- `user_input` (str): The text to search for similar translations
- `target_language` (str): Target language ('chinese' or 'english')
- `top_k` (int): Number of similar pairs to retrieve (1-20, default: 5)

**Returns:**
Dictionary containing pairs, total_found, query_language, and target_language

**Example usage in MCP client:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_similar_pairs",
    "arguments": {
      "user_input": "The Insurance Authority issues this Guideline",
      "target_language": "chinese",
      "top_k": 3
    }
  }
}
```

### 2. get_top_k

Returns the top_k parameter for search configuration.

**Parameters:**
- `user_input` (str): The input text
- `target_language` (str): Target language
- `top_k` (int): Number of results to return

**Returns:** The top_k value

### 3. get_user_input

Returns the user_input parameter.

**Parameters:**
- `user_input` (str): The input text
- `target_language` (str): Target language
- `top_k` (int): Number of results to return

**Returns:** The user input text

### 4. get_target_language

Returns the target_language parameter.

**Parameters:**
- `user_input` (str): The input text
- `target_language` (str): Target language
- `top_k` (int): Number of results to return

**Returns:** The target language

### 5. health_check

Health check for the search service.

**Parameters:** None

**Returns:** Service status information

### 6. get_service_info

Get information about the search service and available tools.

**Parameters:** None

**Returns:** Service information and tool descriptions

## MCP Resources

The server provides the following resources:

### 1. translation://{pair_id}

Get a specific translation pair by ID.

**Example:**
```
translation://123
```

Returns formatted information about translation pair with ID 123.

### 2. search://results/{query}

Get formatted search results for a query.

**Example:**
```
search://results/Insurance Authority
```

Returns formatted search results for the query "Insurance Authority".

## MCP Prompts

The server provides the following prompts:

### 1. search_translation_prompt

Generate a search prompt for finding similar translation pairs.

**Parameters:**
- `text` (str): Text to search for
- `target_language` (str): Target language (default: "chinese")
- `style` (str): Prompt style - "detailed", "simple", or "context" (default: "detailed")

### 2. analyze_translation_quality

Generate a prompt to analyze translation quality between English and Chinese text.

**Parameters:**
- `english_text` (str): English text to analyze
- `chinese_text` (str): Chinese text to analyze

### 3. suggest_search_terms

Generate suggestions for effective search terms in translation databases.

**Parameters:**
- `domain` (str): Domain context (default: "general")
- `language` (str): Language for search terms (default: "english")

## Usage Examples

### Using with MCP-compatible clients

1. **Claude Desktop with MCP:**

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "search-similar-tool": {
      "command": "uv",
      "args": ["run", "server", "search_similar_tool", "stdio"],
      "cwd": "/path/to/search_pairs/search"
    }
  }
}
```

2. **Direct MCP client usage:**

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_search_tool():
    server_params = StdioServerParameters(
        command="python",
        args=["search_similar_tool.py"],
        cwd="/path/to/search_pairs/search"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Call the search tool
            result = await session.call_tool(
                "search_similar_pairs",
                {
                    "user_input": "insurance guidelines",
                    "target_language": "chinese",
                    "top_k": 3
                }
            )
            
            print(result)

# Run the example
asyncio.run(use_search_tool())
```

## Response Format

### Search Results

```json
{
  "pairs": [
    {
      "id": 123,
      "gl_number": "GL001",
      "row_number": "1",
      "version": "1.0",
      "effective_date": "2024-01-01",
      "english_text": "The Insurance Authority issues this Guideline...",
      "chinese_text": "保險業監管局依據《保險業條例》...",
      "context": "The Insurance Authority issues this Guideline...",
      "metadata": {
        "created_at": "2024-01-01T00:00:00"
      }
    }
  ],
  "total_found": 3,
  "query_language": "en",
  "target_language": "chinese"
}
```

## Environment Configuration

Create a `.env` file with the following variables:

```bash
# Database connection
DATABASE_URL=postgresql://username:password@host:port/database

# Optional: Embedding service configuration
EMBEDDING_ENDPOINT=http://10.96.184.114:8007/v1/embeddings
EMBEDDING_MODEL=hosted_vllm/Dmeta
```

## Database Schema

The tool expects a PostgreSQL database with the following table structure:

```sql
CREATE TABLE trans_agent (
    id SERIAL PRIMARY KEY,
    gl_number VARCHAR,
    row_number VARCHAR,
    version VARCHAR,
    effective_date VARCHAR,
    english_text TEXT,
    chinese_text TEXT,
    english_embedding VECTOR(768),
    chinese_embedding VECTOR(768),
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Error Handling

The MCP server handles errors gracefully:

- Invalid parameters return appropriate error messages
- Database connection issues are caught and reported
- Embedding service failures are handled with fallback responses

## Development
docker command

```bash
docker pull ghcr.io/elainexxxxx/search:f5db925
docker run --name search_pairs -p 8000:8000 ghcr.io/elainexxxxx/search:f5db925
```
### Testing

Run tests in development:

```bash
# Test basic functionality
python search_similar_tool.py test

# Test specific tools (requires MCP client setup)
# See examples above for MCP client usage
```

### Adding New Tools

To add new MCP tools, use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def new_tool(param1: str, param2: int) -> str:
    """Description of what the tool does"""
    # Tool implementation
    return result
```

### Adding New Resources

To add new MCP resources, use the `@mcp.resource()` decorator:

```python
@mcp.resource("resource://pattern/{param}")
def new_resource(param: str) -> str:
    """Description of the resource"""
    # Resource implementation
    return content
```

### Adding New Prompts

To add new MCP prompts, use the `@mcp.prompt()` decorator:

```python
@mcp.prompt()
def new_prompt(param1: str, param2: str = "default") -> str:
    """Description of the prompt"""
    # Prompt generation logic
    return prompt_text
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   - Check your `DATABASE_URL` in the `.env` file
   - Ensure the PostgreSQL server is running and accessible
   - Verify the pgvector extension is installed

2. **Embedding Service Errors:**
   - Check if the embedding service is running at the configured endpoint
   - Verify network connectivity to the embedding service

3. **MCP Protocol Issues:**
   - Ensure you're using a compatible MCP client
   - Check that the server is running in stdio mode
   - Verify the client is properly configured

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with MCP clients
5. Submit a pull request

---

For more information about the Model Context Protocol, visit: https://github.com/modelcontextprotocol/specification


