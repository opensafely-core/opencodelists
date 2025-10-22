# Local Deployment Testing Guide

## TL;DR

```bash
# Deploy your current branch locally then access the application at http://localhost:7001 (or the port shown in output)
just local-deploy

# Deploy a specific branch
just local-deploy <BRANCH_NAME>

# Simulate a deployment of your current branch by first deploying the main branch.
# If you just deploy your current branch without first deploying main you are simulating
# a fresh deployment, rather than deploying into an already running instance.
just local-deploy main
just local-deploy

# Force a clean rebuild
FORCE_REBUILD=1 just local-deploy

# Use a different port
HOST_PORT=7002 just local-deploy
```

## What is this?
The local deployment system creates a production-like environment on your local machine using Docker-in-Docker. It simulates the actual production deployment process by:

- Running a Dokku container (our production deployment platform)
- Building the OpenCodelists application as a Docker image
- Deploying that image to the Dokku container
- Setting up proper storage, networking, and environment variables

This lets you test changes to the build and deployment steps by replicating as closely as possible the production process.

## Architecture Overview
```
Your Machine
└── opencodelists-local-deployment (Docker container)
    ├── dokku container (deployment platform)
    ├── otel-collector container (telemetry)
    └── opencodelists container (the app)
```

The system creates a container within a container setup:

- **Host container**: `opencodelists-local-deployment` - provides the Docker-in-Docker environment
- **Inner containers**: `dokku`, `otel-collector`, and your `opencodelists` application

## Available commands

```bash
just local-deploy [branch]

just local-deploy          # Deploy current branch
just local-deploy main     # Deploy main branch
just local-deploy feature  # Deploy feature branch
```

**What it does:**

1. Ensures the container environment exists (sets it up if needed)
2. Builds the chosen branch as a Docker image
3. Deploys it to the local Dokku instance
4. Shows you the access URL

You can also set the following environment variables to customize the deployment:
- `HOST_PORT`: The port on your host machine to map to the application (default is 7001)
- `FORCE_REBUILD`: Set to `1` to force a clean rebuild of everything

```bash
FORCE_REBUILD=1 just local-deploy # Force a clean rebuild and deploy the current branch
HOST_PORT=7002 just local-deploy  # Deploy to a different port
```

## File Structure

```bash
deploy/local/
├── config.sh                   # Shared configuration and functions
├── container-creation.sh       # Container creation and initial setup - called by deploy.sh if needed
├── container-deploy.sh         # Application deployment logic - to be run inside the container
├── container-redeploy.sh       # Branch switching and rebuild logic - to be run inside the container
├── deploy.sh                   # Entry point for deployments - called by the just command
├── docker-compose.yaml         # Dokku and otel-collector services - composed within the container
├── container-redeploy.sh       # Branch switching and rebuild logic - to be run inside the container
└── LOCAL_DEPLOYMENT_TESTING.md # This documentation file
```

## Detailed Process Breakdown

The `just local-deploy` command calls `deploy.sh`.

**deploy.sh**

- If the container is not already running, or the `FORCE_REBUILD` variable is set, or if a different `HOST_PORT` is specified then it will run `container-creation.sh` to set up the Docker container environment.

**container-creation.sh**

- Checks if the `opencodelists-local-deployment` container exists.
- Creates new container if missing, or restarts if stopped
- Starts Docker daemon inside the container
- Sets up git safe directories to avoid ownership warnings
- Maps host port (default 7001) to container port 7000
- Runs the deployment process inside the container by calling `container-deploy.sh`

**container-deploy.sh**

- Installs `just` command runner if not already installed
- Sets up storage directories for the application
- Starts Dokku and otel-collector containers using `docker-compose` _NB the otel-collector is because the app tries sending telemetry data, but if there is nothing listening for it then the logs get polluted with loads of errors so instead we listen and capture them_
- Waits for services to be ready
- Builds OpenCodelists as a production Docker image
- Creates Dokku app and mounts storage
- Sets environment variables
- Deploys image to Dokku
- Configures port mapping

**deploy.sh**
- Now that the container is running it calls `container-redeploy.sh` in the container to handle the actual deployment of the application.

**container-redeploy.sh**
- if no branch is specified, it defaults to the current working directory and builds the production docker image from it
- if a branch is specified it checks out the target branch to a temp directory and then builds the production docker image from that branch
- tags the opencodelists image and deploys to the existing Dokku instance
- cleans up old Docker images to free up space


## Working with Coding System Databases

By default the script does not copy across any coding system databases.

If you need them to test viewing a codelist the best approach is as follows:

1. Attempt to view the codelist in the browser. (This may need to be a published or under review codelist.) - you'll get a 500 error.

If you're feeling brave you can run this script to automatically view the logs, find the missing database, and copy it across. If you're more cautious, move to step 2.

```bash
latest_db=$(docker exec -t opencodelists-local-deployment bash -c "docker logs opencodelists.web.1" | grep -oE 'coding_systems/[^ ]+\.sqlite3' | tail -n1)
if [[ -z "$latest_db" ]]; then
    echo "No missing database found in logs."
else
    echo "Latest missing database: $latest_db"
    echo "Attempting to copy the database file..."
    docker cp "$latest_db" opencodelists-local-deployment:/var/lib/dokku/data/storage/opencodelists/$latest_db
    echo "Database file copied - try to load the codelist again."
fi
```

2. Check the logs for the web service container to see which database is missing by executing the following command:

```bash
docker exec -t opencodelists-local-deployment bash -c "docker logs opencodelists.web.1"
```

You will see an error similar to:

```bash
django.db.utils.OperationalError: no such table: snomedct_description

If this is development then you may be missing the following sqlite database:

- coding_systems/snomedct/snomedct_3920_20241127.sqlite3
```

3. Copy the missing database file. So for the example above you would run:

```bash
MISSING_DB=coding_systems/snomedct/snomedct_3920_20241127.sqlite3
docker cp $MISSING_DB opencodelists-local-deployment:/var/lib/dokku/data/storage/opencodelists/$MISSING_DB
```

## Troubleshooting

The first step is to trigger a rebuild with

```bash
FORCE_REBUILD=1 just local-deploy
```

Other things that may be useful:

```bash
# Check container logs
docker logs opencodelists-local-deployment

# Check inner container logs for the opencodelists app
docker exec -t opencodelists-local-deployment bash -c "docker logs opencodelists.web.1"

# Check inner container logs for the dokku container
docker exec -t opencodelists-local-deployment docker logs dokku
```

## TODO

- These scripts don't do any of the CI stuff from the main.yml and deploy.yml files. A lot of that is linting and testing which can be achieved with `just` commands. But there are some things like the smoke-test which may fail. Currently the smoke-test will fail as soon as you push your branch, so it will be caught before deployment. Therefore it's not essential to replicate that here, but it might be useful to add in the future.
- We might want a command to stop the container. Keeping it running means that redeploys are a lot faster so leaving for now - but it will consume system resources until stopped.
