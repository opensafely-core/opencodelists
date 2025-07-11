#!/bin/bash
set -eu

# Default to running a minimal deployment without full CI pipeline
RUN_CI=${RUN_CI:-0}

if [ "$RUN_CI" = "1" ]; then
    echo "🧪 Running full CI pipeline tests before deployment..."
    ./test-ci-pipeline.sh
    echo "✅ CI pipeline tests passed. Proceeding with deployment..."
else
    echo "⚡ Skipping CI pipeline tests. Use RUN_CI=1 to run them before deployment."
fi

echo "🔄 Building new Docker image with latest changes..."
just docker-build prod
docker tag opencodelists dokku/opencodelists:latest

echo "🚀 Deploying to Dokku..."
# Use || true to ensure script continues even if git:from-image exits with non-zero status
docker exec -t dokku sh -c "dokku git:from-image opencodelists dokku/opencodelists:latest" || true
# Always run ps:rebuild to ensure changes like Procfile updates are applied
echo "🔄 Rebuilding app processes..."
docker exec -t dokku sh -c "dokku ps:rebuild opencodelists"

echo "🧹 Cleaning up old images..."
docker exec -t dokku sh -c "dokku releases:purge opencodelists --keep 2" || true
docker image prune -a -f

echo "✅ Deployment complete!"
echo "   Check app at: http://localhost:7000"
echo "   View logs with: docker exec -t dokku sh -c \"dokku logs opencodelists -t\""
