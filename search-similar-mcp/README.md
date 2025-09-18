# Docker Deployment Guide for Search Similar MCP

This guide explains how to build, deploy, and use the search-similar-mcp Docker image.

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
2. **Environment Variables**: You need to provide the following environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `EMBEDDING_ENDPOINT`: VLLM embedding service endpoint
   - `EMBEDDING_MODEL`: Embedding model name

### Quick Start

1. **Pull the image:**
   ```bash
   docker pull ghcr.io/elainexxxxx/search:54d7b82
   ```

2. **Run the container:**
   ```bash
   docker run --name search-similar-mcp ghcr.io/elainexxxxx/search:54d7b82
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