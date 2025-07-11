#!/bin/bash
set -eu

WORKSPACE="${containerWorkspaceFolder:?containerWorkspaceFolder not set}"
# TEST DEPLOYMENT SCRIPT

# INSTALL JUST
cd /tmp && wget https://github.com/casey/just/releases/download/1.40.0/just-1.40.0-x86_64-unknown-linux-musl.tar.gz && tar -xzf just-1.40.0-x86_64-unknown-linux-musl.tar.gz && chmod 555 just
sudo mv /tmp/just /usr/bin/

cd "$WORKSPACE"
# cp dotenv-sample .env
touch db.sqlite3

sudo mkdir -p /var/lib/dokku/data/storage/opencodelists
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/bnf/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/dmd/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/icd10/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/snomedct/

sudo cp db.sqlite3 /var/lib/dokku/data/storage/opencodelists/

sudo chown -R 10003:10003 /var/lib/dokku/data/storage/opencodelists

# Wait for Docker daemon to be available
max_attempts=30
attempt=1
while ! docker info >/dev/null 2>&1; do
    if [ "$attempt" -ge "$max_attempts" ]; then
        echo "Docker daemon did not start after $max_attempts attempts. Exiting."
        exit 1
    fi
    echo "Waiting for Docker daemon to start... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt+1))
done

docker compose up -d

# Get otel-collector container IP address
otel_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' otel-collector)

just docker-build prod
docker tag opencodelists dokku/opencodelists:latest

docker exec -t dokku sh -c "dokku apps:destroy opencodelists --force" || true
docker exec -t dokku sh -c "dokku apps:create opencodelists"
docker exec -t dokku sh -c "dokku storage:mount opencodelists /var/lib/dokku/data/storage/opencodelists/:/storage"
docker exec -t dokku sh -c "dokku config:set opencodelists BASE_URLS=\"http://localhost:7000,http://127.0.0.1:7000\" DATABASE_DIR=\"/storage\" DATABASE_URL=\"sqlite:////storage/db.sqlite3\" DJANGO_SETTINGS_MODULE=\"opencodelists.settings\" SECRET_KEY=\"thisisatestsecretkeyfortestingonly\" TRUD_API_KEY=\"thisisatesttrudkeyfortestingonly\" OTEL_EXPORTER_OTLP_ENDPOINT=\"http://$otel_ip:4318\""
docker exec -t dokku sh -c "dokku git:from-image opencodelists dokku/opencodelists:latest"
docker image prune -a -f
