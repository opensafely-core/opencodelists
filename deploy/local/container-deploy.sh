#!/bin/bash
set -eu

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/config.sh"

ensure_dockerd_running() {
    if ! pgrep -f dockerd >/dev/null 2>&1; then
        if [ -f /var/run/docker.pid ]; then
            pid=$(cat /var/run/docker.pid)
            if ! ps -p "$pid" >/dev/null 2>&1; then
                log "Removing stale /var/run/docker.pid"
                sudo rm -f /var/run/docker.pid
            else
                log "dockerd process with PID $pid is running."
            fi
        fi
        log "Starting dockerd..."
        dockerd > /var/log/dockerd.log 2>&1 &
        # Wait for dockerd to be ready
        local max_attempts=30
        local attempt=1
        while ! docker info >/dev/null 2>&1; do
            if [ "$attempt" -ge "$max_attempts" ]; then
                log "Docker daemon did not start after $max_attempts attempts. Exiting."
                exit 1
            fi
            log "Waiting for Docker daemon to start... ($attempt/$max_attempts)"
            sleep 2
            attempt=$((attempt+1))
        done
        log "✓ dockerd started"
    else
        log "dockerd is already running."
    fi
}

should_deploy() {
    # 1. Check if services exist at all (fresh build)
    local all_services
    all_services=$(docker compose -f ./deploy/local/docker-compose.yaml ps --services)
    if ! echo "$all_services" | grep -q dokku || ! echo "$all_services" | grep -q otel-collector; then
        log "One or both services do not exist yet (fresh build)."
        return 0
    fi

    # 2. Wait for services to start if they exist but are not running
    local max_attempts=10
    local attempt=1
    while :; do
        local running_services
        running_services=$(docker compose -f ./deploy/local/docker-compose.yaml ps --services --filter "status=running")
        if echo "$running_services" | grep -q dokku && echo "$running_services" | grep -q otel-collector; then
            break  # Both are running, continue to next checks
        fi
        if [ "$attempt" -ge "$max_attempts" ]; then
            log "Not all docker-compose services are running after waiting."
            log "$running_services"
            return 0  # Scenario 3: stuck, trigger redeploy
        fi
        log "Waiting for dokku and otel-collector to start... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt+1))
    done

    # 3. Dokku app not created
    if ! docker exec dokku dokku apps:exists opencodelists >/dev/null 2>&1; then
        log "Dokku app 'opencodelists' does not exist."
        return 0
    fi

    # 4. Dokku app not running
    if ! docker exec dokku dokku ps:report opencodelists | grep -q running; then
        log "Dokku app 'opencodelists' is not running."
        return 0
    fi

    # 5. Dokku app not running on 7000
    local port_map
    port_map=$(docker exec dokku dokku ports:report opencodelists --ports-map 2>/dev/null | grep 7000)
    if [[ -z "$port_map" ]]; then
        log "Dokku app 'opencodelists' is not running on port 7000."
        return 0
    fi

    # None of the conditions met
    return 1
}

install_just() {
    if command -v just >/dev/null 2>&1; then
        log "✓ Just already installed"
        return
    fi

    log "Installing just command runner..."
    local just_url="https://github.com/casey/just/releases/download/${JUST_VERSION}/just-${JUST_VERSION}-x86_64-unknown-linux-musl.tar.gz"

    cd /tmp
    wget "$just_url"
    tar -xzf "just-${JUST_VERSION}-x86_64-unknown-linux-musl.tar.gz"
    chmod +x just
    sudo mv just /usr/bin/
    log "✓ Just installed successfully"
}

setup_storage() {
  cd "$WORKSPACE_DIR"
  log "Setting up storage directories..."

  # Create database file if it doesn't exist
  touch db.sqlite3

  # Create storage directories
  sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/{coding_systems/{bnf,dmd,icd10,snomedct},}

  # Copy database
  sudo cp db.sqlite3 /var/lib/dokku/data/storage/opencodelists/

  # Set permissions
  sudo chown -R 10003:10003 /var/lib/dokku/data/storage/opencodelists

  log "✓ Storage setup complete"
}

deploy_application() {
    log "Starting application deployment..."

    log "Running docker compose to set up dokku and otel-collector..."
    docker compose -f ./deploy/local/docker-compose.yaml up -d

    log "Getting otel-collector IP..."
    local otel_ip
    otel_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' otel-collector)

    log "Building and tagging opencodelists application..."
    just docker-build prod
    docker tag opencodelists dokku/opencodelists:latest

    log "Creating dokku app..."
    docker exec -t dokku sh -c "dokku apps:destroy opencodelists --force" || true
    docker exec -t dokku sh -c "dokku apps:create opencodelists"

    log "Mounting storage for opencodelists in dokku..."
    docker exec -t dokku sh -c "dokku storage:mount opencodelists /var/lib/dokku/data/storage/opencodelists/:/storage"

    log "Setting environment variables in dokku..."
    docker exec -t dokku sh -c "dokku config:set opencodelists \
        BASE_URLS=\"http://localhost:7000,http://127.0.0.1:7000\" \
        DATABASE_DIR=\"/storage\" \
        DATABASE_URL=\"sqlite:////storage/db.sqlite3\" \
        DJANGO_SETTINGS_MODULE=\"opencodelists.settings\" \
        SECRET_KEY=\"thisisatestsecretkeyfortestingonly\" \
        TRUD_API_KEY=\"thisisatesttrudkeyfortestingonly\" \
        OTEL_EXPORTER_OTLP_ENDPOINT=\"http://$otel_ip:4318\""

    log "Deploying application to dokku..."
    docker exec -t dokku sh -c "dokku git:from-image opencodelists dokku/opencodelists:latest"
    docker exec -t dokku sh -c "dokku ports:add opencodelists http:7000:7000"

    log "Cleaning up..."
    docker image prune -a -f

    log "✓ Application deployment complete"
}

ensure_dockerd_running
if should_deploy "${1:-}"; then
    install_just
    setup_storage
    deploy_application
    echo -e "
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🚀 Your current branch is now deployed locally.
║"
else
    log "No deployment needed."
        echo -e "
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🚀 Which ever branch you were running last is now deployed locally.
║"
fi
