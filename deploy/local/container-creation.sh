#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/config.sh"

check_docker_installed

run_container() {
    log "Creating container '$CONTAINER_NAME'..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -v "$(pwd):$WORKSPACE_DIR" \
        -w "$WORKSPACE_DIR" \
        -p "$HOST_PORT:7000" \
        --privileged \
        "$CONTAINER_IMAGE" \
        sleep infinity

    set_git_safe_directory "$CONTAINER_NAME"
    log "✓ Container '$CONTAINER_NAME' created and started"
}

log "Checking container status..."

if ! docker ps -a --format '{{.Names}}' | grep -w "$CONTAINER_NAME" >/dev/null; then
    log "Container does not exist. Pulling image and creating..."
    docker pull "$CONTAINER_IMAGE"
    run_container
elif [[ "${FORCE_REBUILD:-}" == "1" ]]; then
    log "FORCE_REBUILD is set. Recreating container..."
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    docker pull "$CONTAINER_IMAGE"
    run_container
elif ! container_is_running "$CONTAINER_NAME"; then
    log "Container exists but is not running. Recreating..."
    docker start "$CONTAINER_NAME"
    log "✓ Container '$CONTAINER_NAME' restarted"
else
    log "Container already running."
fi

# Run the post-create command inside the container
log "Setting up development environment..."
docker exec -w "$WORKSPACE_DIR" "$CONTAINER_NAME" bash -c "./deploy/local/container-deploy.sh"

end_message "$CONTAINER_NAME"
