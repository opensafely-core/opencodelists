#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/config.sh"

check_docker_installed

# Ensure container is running with correct port
current_port=""
if container_is_running "$CONTAINER_NAME"; then
    current_port=$(get_container_port "$CONTAINER_NAME")
fi

if ! container_is_running "$CONTAINER_NAME" || [[ "${FORCE_REBUILD:-}" == "1" ]] || [[ "$current_port" != "$HOST_PORT" ]]; then
    if [[ "${FORCE_REBUILD:-}" == "1" ]]; then
        log "FORCE_REBUILD is set. Running container-creation.sh..."
    elif [[ "$current_port" != "$HOST_PORT" ]]; then
        log "Container port ($current_port) doesn't match desired port ($HOST_PORT). Recreating..."
        export FORCE_REBUILD=1
    else
        log "Container '$CONTAINER_NAME' does not exist or is not running."
        log "Running container-creation.sh..."
    fi
    "$SCRIPT_DIR/container-creation.sh"
fi

# Not sure why we need to run this again - but otherwise if fails so hey.
set_git_safe_directory "$CONTAINER_NAME"

# Execute redeploy inside container
docker exec -it -w "$WORKSPACE_DIR" "$CONTAINER_NAME" bash -c './deploy/local/container-redeploy.sh "$@"' _ "$@"

end_message "$CONTAINER_NAME"
