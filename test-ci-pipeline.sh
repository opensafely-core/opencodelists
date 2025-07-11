#!/bin/bash
set -eu

# This script replicates the CI build and test pipeline locally
# It runs the same checks and tests as the GitHub Actions workflows

# Function to clean up containers when done
cleanup_smoke_test() {
  echo "🧹 Cleaning up smoke test containers..."
  just docker-stop-test
}

# Set up trap to ensure cleanup happens even if script errors out
trap cleanup_smoke_test EXIT

echo "🔍 Running CI pipeline tests locally..."

# Step 1: Lint checks
echo "⚙️ Running linting and code checks..."
just docker-check-py
just docker-check-js

# Step 2: Build images for both prod and dev
echo "🏗️ Building Docker images for prod and dev..."
just docker-build prod
just docker-build dev

# Step 3: Check migrations
echo "🔄 Checking database migrations..."
just docker-check-migrations

# Step 4: Run unit tests
echo "🧪 Running Python unit tests with migrations..."
just docker-test-py --migrations

# Step 5: Run JS tests
echo "🧪 Running JavaScript tests..."
just docker-test-js

# Step 6: Run the production image on a different port (7001) and smoke test it
echo "🚀 Running production image and smoke tests on port 7001..."

# Using just command with our new serve-test option
just docker-serve-test 7001

# Give the server a moment to start
sleep 5

# Run smoke test against the alternative port
just docker-smoke-test http://localhost:7001 prod-test || { docker logs docker-prod-test-1; echo "❌ Smoke test failed. Fix the issues before deploying."; exit 1; }

# If we got here, all tests passed
echo "✅ All CI tests passed locally!"
echo "   You can now deploy using ./redeploy.sh"
