# Testing Deployment Changes in the Devcontainer

This guide explains how to test changes to deployment configuration (like the Procfile, environment variables, or other Dokku settings) locally before deploying to production.

## Initial Setup

When the devcontainer starts, the `test-deploy.sh` script automatically:

1. Sets up necessary dependencies (`just`)
2. Creates required directories and permissions
3. Starts Dokku and otel-collector containers
4. Builds the app image and deploys it to Dokku

This provides a local environment that replicates the production Dokku setup.

## Testing Deployment Changes

### Workflow

1. **Make your changes**
   - Edit the `Procfile`, Dockerfile, or other deployment configuration
   - All files should be edited in the workspace, not inside containers

2. **Run CI checks (optional but recommended)**
   - Run `./test-ci-pipeline.sh` to execute all the CI checks locally
   - This runs the same checks as GitHub Actions workflows (linting, tests, migrations)
   - Note: The CI pipeline will run smoke tests on port 7001 to avoid conflicts with Dokku

   Or run individual checks:
   ```bash
   just docker-check-py      # Python linting and checks
   just docker-check-js      # JavaScript linting and checks
   just docker-test-py       # Python unit tests
   just docker-test-js       # JavaScript tests
   ```

3. **Redeploy to local Dokku**
   - Run `./redeploy.sh` to build, test, and deploy your changes
   - Run `RUN_CI=1 ./redeploy.sh` to run the full CI pipeline before deploying

4. **Verify the changes**
   - Access the app at http://localhost:7000
   - Check logs with `docker exec -t dokku sh -c "dokku logs opencodelists -t"`
   - For release phase logs: `docker exec -t dokku sh -c "dokku logs opencodelists --process release"`

### Port Configurations

The testing environment uses the following port configurations:
- Dokku deployment: Runs on port 7000
- CI smoke tests: Run on port 7001 to avoid conflicts with the Dokku deployment

You can run smoke tests manually on a custom port using:
```bash
# Run smoke tests on port 7001 (default)
just docker-serve-test

# Run smoke tests on a custom port
just docker-serve-test 7002

# Stop the smoke test container
just docker-stop-test
```

### Common Tasks

#### Testing Procfile Changes

```bash
# 1. Edit the Procfile
# 2. Redeploy
./redeploy.sh
# 3. Check if the release phase ran successfully
docker exec -t dokku sh -c "dokku logs opencodelists --process release"
```

#### Testing Environment Variable Changes

```bash
# Set new environment variables
docker exec -t dokku sh -c "dokku config:set opencodelists NEW_VAR=value"

# List all environment variables
docker exec -t dokku sh -c "dokku config opencodelists"
```

#### Checking Container Status

```bash
# List all Dokku apps
docker exec -t dokku sh -c "dokku apps:list"

# Check app status
docker exec -t dokku sh -c "dokku ps opencodelists"
```

## Troubleshooting

### Image Not Found
If Dokku can't find your image, verify the image exists locally:
```bash
docker images | grep opencodelists
```

### Dokku App Not Starting
Check for errors in the logs:
```bash
docker exec -t dokku sh -c "dokku logs opencodelists -t"
```

### Process Types Not Recognized
Ensure your Procfile is properly included in the image:
```bash
docker run --rm dokku/opencodelists:latest cat /app/Procfile
```
