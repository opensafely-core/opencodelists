#!/bin/bash
set -eu

# Default to running a minimal deployment without full CI pipeline
RUN_CI=${RUN_CI:-0}
# Accept target branch as parameter, default to current branch
TARGET_BRANCH=${1:-$(git rev-parse --abbrev-ref HEAD)}

# Store original directory
ORIGINAL_DIR="$PWD"

# Function to clean up when done
cleanup() {
  echo "Ensure staticfiles directory exists and the .keep file hasn't been overwritten"
  mkdir -p docker/docker-staticfiles
  touch docker/docker-staticfiles/.keep

  # If we created a temp dir, clean it up
  if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    echo "Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
  fi

  # Return to original directory
  cd "$ORIGINAL_DIR"
}

# Set up trap to ensure cleanup happens even if script errors out
trap cleanup EXIT

# If testing a different branch than current, set up temp directory
if [ "$TARGET_BRANCH" != "$(git rev-parse --abbrev-ref HEAD)" ]; then
  echo "> Testing deployment for branch: $TARGET_BRANCH"

  # Make sure we have all remote branches fetched in the original repository
  echo "> Fetching all remote branches..."
  cd "$ORIGINAL_DIR"
  git fetch --all --prune

  # Create a local branch from the remote TARGET_BRANCH if it doesn't exist locally
  if ! git rev-parse --verify --quiet "$TARGET_BRANCH" >/dev/null; then
    echo "> Creating local copy of remote branch: $TARGET_BRANCH"
    git branch "$TARGET_BRANCH" "origin/$TARGET_BRANCH"
  fi

  # Verify we now have the branch locally
  if ! git rev-parse --verify --quiet "$TARGET_BRANCH" >/dev/null; then
    echo "❌ Could not find or create branch: $TARGET_BRANCH"
    exit 1
  fi

  # Create a temporary directory and clone the repository
  TEMP_DIR=$(mktemp -d)
  echo "> Creating temporary workspace at $TEMP_DIR"

  # Clone the repository into the temp dir (shallow clone for speed)
  git clone "$PWD" "$TEMP_DIR"
  cd "$TEMP_DIR"

  # Fetch the target branch and check it out
  echo "> Checking out branch: $TARGET_BRANCH"
  git fetch origin "$TARGET_BRANCH":refs/remotes/origin/"$TARGET_BRANCH" --depth 1
  git checkout -b "$TARGET_BRANCH" origin/"$TARGET_BRANCH" || {
    echo "❌ Failed to checkout branch $TARGET_BRANCH"
    exit 1
  }

  echo "✅ Now working with code from branch: $TARGET_BRANCH"
else
  echo "> Using current branch: $TARGET_BRANCH"
fi

if [ "$RUN_CI" = "1" ]; then
    echo "> Running full CI pipeline tests before deployment..."
    ./local-ci-pipeline.sh
    echo "> CI pipeline tests passed. Proceeding with deployment..."
else
    echo "> Skipping CI pipeline tests. Use RUN_CI=1 to run them before deployment."
    echo "> Building new Docker image with latest changes..."
    just docker-build prod
fi

# Tag the built prod image for local dokku deployment
docker tag opencodelists dokku/opencodelists:latest

echo "> Deploying to Dokku..."
# Use || true to ensure script continues even if git:from-image exits with non-zero status
docker exec -t dokku sh -c "dokku git:from-image opencodelists dokku/opencodelists:latest" || true
# Always run ps:rebuild to ensure changes like Procfile updates are applied
echo "> Rebuilding app processes..."
docker exec -t dokku sh -c "dokku ps:rebuild opencodelists"

echo "> Cleaning up old images..."
docker exec -t dokku sh -c "dokku releases:purge opencodelists --keep 2" || true
docker image prune -a -f

echo "✅ Deployment complete!"
echo "   Branch tested: $TARGET_BRANCH"
echo "   Check app at: http://localhost:7000"
echo "   View logs with: docker exec -t dokku sh -c \"dokku logs opencodelists -t\""
