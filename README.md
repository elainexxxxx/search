# Search Similar Tool Server

This tool helps find the most relevant translation pairs from a database based on input text.

## Project Structure

```
search_pairs/
├── search_similar_tool.py      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image configuration
├── docker-compose.yml          # Docker Compose setup
├── .dockerignore              # Docker build exclusions
├── .env                       # Environment variables (create manually)
└── README.md                  # This documentation
```

## Features

- **Language Detection**: Automatically detects whether input text is Chinese or English
- **Embedding Search**: Uses vector embeddings to find semantically similar translation pairs
- **Multiple Endpoints**: Provides various endpoints for different use cases
- **RESTful API**: Easy to integrate with any application via HTTP requests

## Quick Start
#### Pull and Run from Docker Hub
```bash
# Pull the pre-built image (replace 'your-username' with actual Docker Hub username)
docker pull ghcr.io/elainexxxxx/search-similar-tool:latest

# Run the container
docker run --name search-similar-tool -p 8060:8060 ghcr.io/elainexxxxx/search-similar-tool:latest
```
## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the server is running and healthy.

#### Python Example:
```python
import requests

response = requests.get("http://localhost:8060/health")
print(response.json())
# Output: {"status": "healthy", "service": "search_similar_tool"}
```

#### Curl Example:
```bash
curl -X GET "http://localhost:8060/health"
```

---

### 2. Root Information

**GET** `/`

Get information about the API and available endpoints.

#### Python Example:
```python
import requests

response = requests.get("http://localhost:8060/")
result = response.json()
print(f"Service: {result['service']}")
print(f"Available endpoints: {list(result['endpoints'].keys())}")
```

#### Curl Example:
```bash
curl -X GET "http://localhost:8060/"
```

---

### 3. Get Top K Parameter

**POST** `/get_top_k`

Returns the `top_k` parameter from the request.

#### Request Body:
```json
{
  "user_input": "Your text here",
  "target_language": "chinese",
  "top_k": 5
}
```

#### Python Example:
```python
import requests

payload = {
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
}

response = requests.post("http://localhost:8060/get_top_k", json=payload)
result = response.json()
print(f"Top K: {result['value']}")
# Output: Top K: 3
```

#### Curl Example:
```bash
curl -X POST "http://localhost:8060/get_top_k" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
  }'
```

---

### 4. Get User Input

**POST** `/get_user_input`

Returns the `user_input` parameter from the request.

#### Python Example:
```python
import requests

payload = {
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
}

response = requests.post("http://localhost:8060/get_user_input", json=payload)
result = response.json()
print(f"User Input: {result['value']}")
# Output: User Input: The Insurance Authority issues this Guideline
```

#### Curl Example:
```bash
curl -X POST "http://localhost:8060/get_user_input" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
  }'
```

---

### 5. Get Target Language

**POST** `/get_target_language`

Returns the `target_language` parameter from the request.

#### Python Example:
```python
import requests

payload = {
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
}

response = requests.post("http://localhost:8060/get_target_language", json=payload)
result = response.json()
print(f"Target Language: {result['value']}")
# Output: Target Language: chinese
```

#### Curl Example:
```bash
curl -X POST "http://localhost:8060/get_target_language" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "The Insurance Authority issues this Guideline",
    "target_language": "chinese",
    "top_k": 3
  }'
```

---

### 6. Get Similar Translation Pairs (Main Function)

**POST** `/get_pairs`

Finds the top-k most similar translation pairs based on embedding similarity.

#### Request Body:
```json
{
  "user_input": "Text to search for similar translations",
  "target_language": "chinese" | "english",
  "top_k": 5
}
```

#### Response:
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

#### Python Example:
```python
import requests
import json

# English input example
payload = {
    "user_input": "The Insurance Authority issues this Guideline pursuant to section 133 of the Insurance Ordinance",
    "target_language": "chinese",
    "top_k": 3
}

response = requests.post("http://localhost:8060/get_pairs", json=payload)
result = response.json()

print(f"Found {result['total_found']} similar pairs")
print(f"Query language detected: {result['query_language']}")
print(f"Target language: {result['target_language']}")

for i, pair in enumerate(result['pairs'], 1):
    print(f"\nPair {i}:")
    print(f"  ID: {pair['id']}")
    print(f"  GL Number: {pair['gl_number']}")
    print(f"  English: {pair['english_text'][:100]}...")
    print(f"  Chinese: {pair['chinese_text'][:100]}...")

# Chinese input example
chinese_payload = {
    "user_input": "保險業監管局依據《保險業條例》第133條發出本指引",
    "target_language": "english",
    "top_k": 2
}

response = requests.post("http://localhost:8060/get_pairs", json=chinese_payload)
result = response.json()
print(f"\nChinese input - Found {result['total_found']} pairs")
print(f"Detected language: {result['query_language']}")
```

#### Curl Example:
```bash
# English input
curl -X POST "http://localhost:8060/get_pairs" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "The Insurance Authority issues this Guideline pursuant to section 133 of the Insurance Ordinance",
    "target_language": "chinese",
    "top_k": 3
  }'

# Chinese input
curl -X POST "http://localhost:8060/get_pairs" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "保險業監管局依據《保險業條例》第133條發出本指引",
    "target_language": "english",
    "top_k": 2
  }'
```

## Parameters

### SearchRequest Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_input` | string | Yes | - | The text to search for similar translations |
| `target_language` | string | Yes | - | Target language: "chinese" or "english" |
| `top_k` | integer | No | 5 | Number of similar pairs to retrieve (1-20) |

## Response Models

### BasicResponse
```json
{
  "value": "any_value"
}
```

### PairsResponse
```json
{
  "pairs": [
    {
      "id": "integer",
      "gl_number": "string",
      "row_number": "string", 
      "version": "string",
      "effective_date": "string",
      "english_text": "string",
      "chinese_text": "string",
      "context": "string",
      "metadata": "object"
    }
  ],
  "total_found": "integer",
  "query_language": "string",
  "target_language": "string"
}
```

## Testing

Run the comprehensive test suite:

```bash
python test_search_similar_tool.py
```

The test suite includes:
- Health check
- All endpoint functionality tests
- Language detection tests
- Error handling tests

## Docker Deployment

### Building the Docker Image

```bash
# Build the image locally
docker build -t search-similar-tool .

# Or tag it for pushing to a registry
docker build -t your-username/search-similar-tool:latest .
```

### Running with Docker

#### Basic Run
```bash
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  search-similar-tool
```

#### Run with Custom Database URL
```bash
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  -e DATABASE_URL="postgresql://username:password@host:port/database" \
  search-similar-tool
```

#### Run with Environment File
```bash
# Create a .env file with your configuration
echo "DATABASE_URL=postgresql://username:password@host:port/database" > .env

# Run with environment file
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  --env-file .env \
  search-similar-tool
```

### Docker Compose Deployment

#### Using the provided docker-compose.yml
```bash
# Start the service in the background
docker-compose up -d

# Start with custom environment variables
DATABASE_URL="postgresql://username:password@host:port/database" docker-compose up -d

# View logs
docker-compose logs -f search-similar-tool

# Stop the service
docker-compose down

# Restart the service
docker-compose restart search-similar-tool
```

### Publishing to Docker Registry

#### Docker Hub
```bash
# Login to Docker Hub
docker login

# Tag your image
docker tag search-similar-tool your-username/search-similar-tool:latest

# Push to Docker Hub
docker push your-username/search-similar-tool:latest
```

#### Private Registry
```bash
# Tag for private registry
docker tag search-similar-tool registry.example.com/search-similar-tool:latest

# Push to private registry
docker push registry.example.com/search-similar-tool:latest
```

### Pulling from Another Linux Server

#### From Docker Hub
```bash
# Pull the latest image
docker pull your-username/search-similar-tool:latest

# Run the pulled image
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  -e DATABASE_URL="postgresql://admin:Abc123@10.96.184.114:5431/ai_platform" \
  your-username/search-similar-tool:latest
```

#### From Private Registry
```bash
# Login to private registry if required
docker login registry.example.com

# Pull the image
docker pull registry.example.com/search-similar-tool:latest

# Run the image
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  -e DATABASE_URL="postgresql://admin:Abc123@10.96.184.114:5431/ai_platform" \
  registry.example.com/search-similar-tool:latest
```

### Docker Container Management

#### Container Operations
```bash
# Check container status
docker ps

# View container logs
docker logs search-similar-tool

# Follow logs in real-time
docker logs -f search-similar-tool

# Stop the container
docker stop search-similar-tool

# Start the container
docker start search-similar-tool

# Restart the container
docker restart search-similar-tool

# Remove the container
docker rm search-similar-tool
```

#### Health Check
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' search-similar-tool

# Manual health check
curl http://localhost:8060/health
```

### Environment Variables

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://admin:Abc123@10.96.184.114:5431/ai_platform` | PostgreSQL connection string |
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent Python from writing .pyc files |
| `PYTHONUNBUFFERED` | `1` | Force Python stdout/stderr to be unbuffered |

### Troubleshooting

#### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   docker run -d --name search-similar-tool -p 8061:8060 search-similar-tool
   ```

2. **Database connection issues**
   ```bash
   # Check logs for connection errors
   docker logs search-similar-tool
   
   # Verify database URL is correct
   docker exec search-similar-tool env | grep DATABASE_URL
   ```

3. **Container won't start**
   ```bash
   # Check container logs
   docker logs search-similar-tool
   
   # Run interactively to debug
   docker run -it --rm search-similar-tool /bin/bash
   ```

#### Performance Tuning

```bash
# Run with memory limit
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  --memory="512m" \
  --cpus="1.0" \
  search-similar-tool

# Run with restart policy
docker run -d \
  --name search-similar-tool \
  -p 8060:8060 \
  --restart=unless-stopped \
  search-similar-tool
```

## Dependencies

- FastAPI
- uvicorn
- requests
- pydantic
- sqlalchemy
- pgvector
- numpy
- python-dotenv

## Environment Setup

Make sure to set up your database connection in the environment variables or `.env` file:

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `422`: Validation error (invalid parameters)
- `500`: Server error

Error responses include detailed error messages to help with debugging.

## Interactive API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8060/docs`
- ReDoc: `http://localhost:8060/redoc`

These provide interactive documentation where you can test the API directly from your browser.