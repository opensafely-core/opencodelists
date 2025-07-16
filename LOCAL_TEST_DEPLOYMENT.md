# Testing Deployment Changes in the Devcontainer

This guide explains how to test changes to deployment configuration (like the Procfile, environment variables, or other Dokku settings) locally before deploying to production.

## Initial Setup

Start the devcontainer either in VS Code or GitHub Codespaces. The devcontainer is configured to run a local Dokku instance, allowing you to test deployment changes without affecting the production environment.

When the devcontainer starts, the `local-deploy.sh` script automatically:

1. Sets up necessary dependencies (`just`)
2. Creates required directories and permissions
3. Starts Dokku and otel-collector containers
4. Builds the app image and deploys it to Dokku

This provides a local environment that replicates the production Dokku setup.

## Testing Deployment Changes

### Workflow

1. **Make your changes**
   - Edit the `Procfile`, Dockerfile, or other deployment configuration

2. **Run CI checks (optional but recommended)**
   - Run `./local-ci-pipeline.sh` to execute all the CI checks locally
   - This runs the same checks as GitHub Actions workflows (linting, tests, migrations)
   - Note: The CI pipeline will run smoke tests on port 7001 to avoid conflicts with Dokku

3. **Redeploy to local Dokku**
   - Run `./local-redeploy.sh` to build, test, and deploy your changes
   - Run as `RUN_CI=1 ./local-redeploy.sh` to run the full CI pipeline before deploying

4. **Verify the changes**
   - Access the app at http://localhost:7000
   - Check logs with `docker exec -t dokku sh -c "dokku logs opencodelists -t"`

### Testing Remote Branches

You can also test deployment changes from any remote branch:

```bash
# Test deployment of a specific remote branch
./local-redeploy.sh branch-name

# Test deployment of a specific remote branch with full CI pipeline
RUN_CI=1 ./local-redeploy.sh branch-name
```

The script will:
1. Fetch the remote branch if it doesn't exist locally
2. Create a temporary workspace with the branch's code
3. Run the deployment process on that branch's code
4. Clean up the temporary workspace automatically when done

This allows you to test deployment changes from pull requests or experimental branches.

### Port Configurations

The testing environment uses the following port configurations:
- Dokku deployment: Runs on port 7000
- CI smoke tests: Run on port 7001 to avoid conflicts with the Dokku deployment

## Troubleshooting

### Database Locks
Occasionally the smoke test fails because the database is locked. This typically happens when multiple processes try to access the SQLite database simultaneously. If this occurs:
- Wait a few seconds and run the script again
- The test environment uses separate storage directories to prevent conflicts

### Branch Checkout Issues
If you encounter issues checking out a specific branch:
- Ensure the branch exists on the remote (run `git fetch --all` first)
- Check that you have permissions to access the branch
- The script will automatically create a local copy of remote branches
