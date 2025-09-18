#!/bin/bash
set -eu

# This script replicates the CI build and test pipeline locally. It runs the
# same checks and tests as the GitHub Actions workflows in main.yml

# Function to clean up containers when done
cleanup() {
  echo "> Cleaning up smoke test containers..."
  just docker-stop-test

  echo "Ensure staticfiles directory exists and the .keep file hasn't been overwritten"
  mkdir -p docker/docker-staticfiles
  touch docker/docker-staticfiles/.keep
}

# Set up trap to ensure cleanup happens even if script errors out
trap cleanup EXIT

echo "> Running jobs from main.yml locally..."

echo "> Simulating job 'check-py' from main.yml"
just docker-check-py

echo "> Simulating job 'check-js' from main.yml"
just docker-check-js

echo "> Simulating job 'test-py' from main.yml"
# Step 1: Build images for both prod and dev
just docker-build prod
just docker-build dev

# Step 2: Check migrations
just docker-check-migrations

# Step 3: Run unit tests
just docker-test-py --migrations

# Step 4: Run smoke test
# The command in main.yml is
#   just docker-serve prod -d
# But that won't work because port 7000 is already in use by the locally
# running dokku instance.
# So we run the test server on port 7001 instead with a slightly different just
# command.
just docker-serve-test 7001
sleep 5
just docker-smoke-test http://localhost:7001 prod-test || { docker logs docker-prod-test-1; echo "❌ Smoke test failed."; exit 1; }

# Step 5: Save docker image
# We currently don't test this step locally
# Step 6: Upload docker image
# This is not applicable for local testing, so we skip it

echo "> Simulating job 'test-js' from main.yml"
just docker-test-js

# If we got here, all tests passed
echo "✅  All CI tests passed locally!"
