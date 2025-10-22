#!/bin/bash
set -eu

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/config.sh"

# Accept target branch as parameter, default to current branch
TARGET_BRANCH=${1:-$(git rev-parse --abbrev-ref HEAD)}
ORIGINAL_DIR="$PWD"
TEMP_DIR=""

# Function to clean up when done
cleanup() {
  # If we created a temp dir, clean it up
  if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi

  # Return to original directory
  cd "$ORIGINAL_DIR"
}

# Set up trap to ensure cleanup happens even if script errors out
trap cleanup EXIT

setup_branch() {
    local target_branch="$1"
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    if [ "$target_branch" != "$current_branch" ]; then
        log "> Testing deployment for branch: $target_branch"

        TEMP_DIR=$(mktemp -d)
        log "> Creating temporary workspace at $TEMP_DIR"

        git clone "$ORIGINAL_DIR" "$TEMP_DIR"
        cd "$TEMP_DIR"

        log "> Checking out branch: $target_branch"
        git remote set-url origin "https://github.com/opensafely-core/opencodelists.git"
        git fetch --all --prune
        git checkout "$target_branch"
        log "✅ Now working with code from branch: $target_branch"
    else
        log "> Using current branch: $target_branch"
    fi
}

deploy() {
    log "> Building new Docker image with latest changes..."
    just docker-build prod

    log "> Deploying to Dokku..."
    docker tag opencodelists dokku/opencodelists:latest
    docker exec -t dokku sh -c "dokku git:from-image opencodelists dokku/opencodelists:latest" || true
    docker exec -t dokku sh -c "dokku ps:rebuild opencodelists"

    log "> Cleaning up old images..."
    docker image prune -a -f
}

# Main execution
setup_branch "$TARGET_BRANCH"
deploy

echo -e "
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🚀 The branch ${YELLOW}'$TARGET_BRANCH'${RESET} is now deployed locally.
║"
