#!/bin/bash

export CONTAINER_NAME="opencodelists-local-deployment"
export CONTAINER_IMAGE="mcr.microsoft.com/devcontainers/universal:3"
export HOST_PORT="${HOST_PORT:-7001}"
export WORKSPACE_DIR="/workspaces/opencodelists"
export JUST_VERSION="1.40.0"

set_git_safe_directory() {
    local container_name="$1"
    docker exec "$container_name" git config --global --add safe.directory "$WORKSPACE_DIR" 2>/dev/null || true
    docker exec "$container_name" git config --global --add safe.directory "$WORKSPACE_DIR/.git" 2>/dev/null || true
}

container_is_running() {
    local container_name="$1"
    docker exec "$container_name" true 2>/dev/null
}

get_container_port() {
    local container_name="$1"
    docker port "$container_name" 7000/tcp 2>/dev/null | head -1 | cut -d: -f2
}

check_docker_installed() {
  if ! command -v docker &> /dev/null; then
      echo "Docker is not installed. Please install Docker first."
      exit 1
  fi
}

export GREEN='\033[1;92m'
export WHITE='\033[1;97m'
export BLUE='\033[1;34m'
export YELLOW='\033[1;93m'
export RESET='\033[0m'
log() { echo -e "${BLUE}[INFO]${RESET} ${WHITE}$*${RESET}"; }

end_message() {
  local container_name="$1"
  local current_port
  current_port=$(get_container_port "$container_name")
  echo -e "║ The container ${GREEN}'$container_name'${RESET} is running dokku.
║ Within that container, there is a container running opencodelists.
║ You can access the application at:
║
║     ${WHITE}http://localhost:$current_port${RESET}
║
╚═════════════════════════════════════════════════════════════════════════════╝
"
}
