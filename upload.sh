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
docker build -t "$IMAGE_NAME" .


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
docker push "$IMAGE_NAME"

echo "Docker image pushed: $IMAGE_NAME"