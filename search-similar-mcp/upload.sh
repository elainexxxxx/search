#!/bin/bash

# Exit on error
set -e

# Get commit message from argument or prompt
if [ -z "$1" ]; then
  read -p "Enter commit message: " COMMIT_MSG
else
  COMMIT_MSG="$1"
fi


# GitHub login (if needed)
if ! git ls-remote &> /dev/null; then
  echo "You are not authenticated with GitHub. Please login."
  if command -v gh &> /dev/null; then
    gh auth login
  else
    echo "Please install GitHub CLI (gh) for easier authentication: https://cli.github.com/"
    exit 1
  fi
fi

# Commit and push code
git add .
git commit -m "$COMMIT_MSG"
git push

# Get latest commit hash (short)
COMMIT_HASH=$(git rev-parse --short HEAD)

# Get GitHub repo info for image naming
GIT_REMOTE=$(git config --get remote.origin.url)
# Extract org/repo from URL (supports HTTPS and SSH)
if [[ "$GIT_REMOTE" =~ github.com[/:]([^/]+)/([^.]+) ]]; then
  GH_ORG="${BASH_REMATCH[1]}"
  GH_REPO="${BASH_REMATCH[2]}"
else
  echo "Could not parse GitHub remote URL: $GIT_REMOTE"
  exit 1
fi

# Compose image name dynamically
IMAGE_NAME="ghcr.io/$GH_ORG/$GH_REPO:$COMMIT_HASH"

# Build Docker image
echo "Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

# Also tag as latest
LATEST_IMAGE="ghcr.io/$GH_ORG/$GH_REPO:latest"
docker tag "$IMAGE_NAME" "$LATEST_IMAGE"


# Docker login to GitHub Container Registry (ghcr.io)
if ! docker info 2>&1 | grep -q 'ghcr.io'; then
  echo "Logging in to GitHub Container Registry (ghcr.io)"
  echo -n "Enter your GitHub username: "
  read GH_USER
  echo "Create a GitHub personal access token (with 'write:packages', 'read:packages', 'delete:packages', and 'repo' scopes) at https://github.com/settings/tokens"
  echo -n "Enter your GitHub personal access token: "
  read -s GH_TOKEN
  echo
  echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
fi

# Push Docker image
echo "Pushing Docker image: $IMAGE_NAME"
docker push "$IMAGE_NAME"

echo "Pushing latest tag: $LATEST_IMAGE"
docker push "$LATEST_IMAGE"

echo "Docker images pushed successfully!"
echo "  - $IMAGE_NAME"
echo "  - $LATEST_IMAGE"
echo ""
echo "To pull and run this image:"
echo "  docker pull $IMAGE_NAME"
echo "  docker run -d --name search-similar-mcp \\"
echo "    -e DATABASE_URL='postgresql://admin:Abc123@10.96.184.114:5431/ai_platform' \\"
echo "    -e EMBEDDING_ENDPOINT='http://10.96.184.114:8007/v1/embeddings' \\"
echo "    -e EMBEDDING_MODEL='hosted_vllm/Dmeta' \\"
echo "    $IMAGE_NAME"