#!/bin/bash
set -eu

cd /tmp && wget https://github.com/casey/just/releases/download/1.40.0/just-1.40.0-x86_64-unknown-linux-musl.tar.gz && tar -xzf just-1.40.0-x86_64-unknown-linux-musl.tar.gz && chmod 555 just
sudo mv /tmp/just /usr/bin/

cd /workspaces/opencodelists
cp dotenv-sample .env
touch db.sqlite3 # workaround because build-dbs-for-local-development expects a db.sqlite3
yes Y | just build-dbs-for-local-development nuclear

docker-compose up -d

docker exec -t dokku sh -c "dokku apps:create opencodelists"
docker exec -t dokku sh -c 'dokku config:set opencodelists BASE_URLS="http://localhost:7000,http://127.0.0.1:7000" DATABASE_DIR="/storage" DATABASE_URL="sqlite:////storage/db.sqlite3" DJANGO_SETTINGS_MODULE="opencodelists.settings" SECRET_KEY="thisisatestsecretkeyfortestingonly" TRUD_API_KEY="thisisatesttrudkeyfortestingonly"'

sudo mkdir -p /var/lib/dokku/data/storage/opencodelists
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/bnf/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/dmd/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/icd10/
sudo mkdir -p /var/lib/dokku/data/storage/opencodelists/coding_systems/snomedct/

sudo cp db.sqlite3 /var/lib/dokku/data/storage/opencodelists/
sudo cp coding_systems/bnf/bnf_test_20200101.sqlite3 /var/lib/dokku/data/storage/opencodelists/coding_systems/bnf/
sudo cp coding_systems/dmd/dmd_test_20200101.sqlite3 /var/lib/dokku/data/storage/opencodelists/coding_systems/dmd/
sudo cp coding_systems/icd10/icd10_test_20200101.sqlite3 /var/lib/dokku/data/storage/opencodelists/coding_systems/icd10/
sudo cp coding_systems/snomedct/snomedct_test_20200101.sqlite3 /var/lib/dokku/data/storage/opencodelists/coding_systems/snomedct/

sudo chown -R 10003:10003 /var/lib/dokku/data/storage/opencodelists

cd /workspaces/opencodelists/docker
just build prod

docker exec -t dokku sh -c "dokku storage:mount opencodelists /var/lib/dokku/data/storage/opencodelists/:/storage"
docker exec -t dokku sh -c "dokku git:from-image opencodelists opencodelists:latest"
