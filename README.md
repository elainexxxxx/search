# Search Similar MCP Server

A Model Context Protocol (MCP) server that provides search functionality for finding similar translation pairs using embeddings. This server can be deployed as a Docker container and used with any MCP-compatible client

## Project Structure

```
search-similar-mcp/
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── env.example        # Environment variables template
├── README.md          # This file
└── upload.sh          # Docker build and push script
```

## Quick Start

### Option 1: Using Docker (Recommended)

1. **Copy environment configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t search-similar-mcp .
   ```

3. **Run the container:**
   ```bash
   docker run --env-file .env search-similar-mcp
   ```

### Option 2: Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

## Environment Variables

The following environment variables are required:

- `DATABASE_URL`: PostgreSQL connection string with pgvector support
- `EMBEDDING_ENDPOINT`: URL to your embedding service (e.g., VLLM endpoint)
- `EMBEDDING_MODEL`: Name of the embedding model to use

Example:
```
DATABASE_URL=postgresql://admin:password@localhost:5432/ai_platform
EMBEDDING_ENDPOINT=http://localhost:8007/v1/embeddings
EMBEDDING_MODEL=hosted_vllm/Dmeta
```

## Building and Uploading the Image

The project includes an automated upload script that will:
1. Commit and push your code to GitHub
2. Build a Docker image tagged with the commit hash
3. Push the image to GitHub Container Registry (ghcr.io)

To build and upload:

```bash
# Make the script executable (if on Linux/Mac)
chmod +x upload.sh

# Run the upload script
./upload.sh "Your commit message"
```

## Using the Docker Image

### Prerequisites

1. **GitHub Container Registry Access**: The image will be available at `ghcr.io/[owner]/[repo-name]`
2. **Environment Variables**: You need to provide the required environment variables listed above

### Quick Start

1. **Pull the image:**
   ```bash
   docker pull ghcr.io/elainexxxxx/search:latest
   ```

2. **Run the container:**
   ```bash
   docker run --name search-similar-mcp \
     -e DATABASE_URL="your_database_url" \
     -e EMBEDDING_ENDPOINT="your_embedding_endpoint" \
     -e EMBEDDING_MODEL="your_embedding_model" \
     ghcr.io/elainexxxxx/search:latest
   ```


### Health Check

The container includes a health check that verifies:
- Database connectivity
- Service availability

Check container health:
```bash
docker ps
docker logs search-similar-mcp
```

### Interacting with the MCP Server

The MCP server runs with stdio transport by default. To interact with it:

1. **For development/testing:**
   ```bash
   docker exec -it search-similar-mcp python search_similar_tool.py
   ```

2. **For MCP client integration:**
   Configure your MCP client to connect to the running container using the appropriate transport method.

### Available MCP Tools

The server provides these tools:
- `search_similar_pairs`: Find similar translation pairs
- `get_translation_pair`: Get specific translation pair by ID
- `health_check`: Check service health
- `get_service_info`: Get service information

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `EMBEDDING_ENDPOINT` | VLLM embedding service URL | `http://10.96.184.114:8007/v1/embeddings` |
| `EMBEDDING_MODEL` | Embedding model name | `hosted_vllm/Dmeta` |

### Troubleshooting

1. **Container won't start:**
   - Check environment variables are set correctly
   - Verify database and embedding service are accessible
   - Check logs: `docker logs search-similar-mcp`

2. **Database connection issues:**
   - Ensure the DATABASE_URL is correct
   - Verify network connectivity to the database
   - Check database credentials and permissions

3. **Embedding service issues:**
   - Verify EMBEDDING_ENDPOINT is accessible
   - Check EMBEDDING_MODEL is correct
   - Test endpoint manually: `curl [EMBEDDING_ENDPOINT]`

### Production Considerations

1. **Security:**
   - Use secrets management for sensitive environment variables
   - Run container as non-root user (already configured)
   - Use specific image tags instead of `:latest` in production

2. **Networking:**
   - Ensure proper network security groups/firewall rules
   - Consider using Docker networks for service isolation

3. **Monitoring:**
   - Monitor container health and logs
   - Set up alerts for service failures
   - Use the built-in health check endpoint