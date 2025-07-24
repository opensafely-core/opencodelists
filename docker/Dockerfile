# syntax=docker/dockerfile:1.2
#################################################
#
# Create base image with python installed.
#
# DL3007 ignored because base-docker we specifically always want to build on
# the latest base image, by design.
#
# hadolint ignore=DL3007
FROM ghcr.io/opensafely-core/base-docker:22.04 as base-python

# we are going to use an apt cache on the host, so disable the default debian
# docker clean up that deletes that cache on every apt install
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Add deadsnakes PPA for installing new Python versions
# ensure fully working base python3 installation
# see: https://gist.github.com/tiran/2dec9e03c6f901814f6d1e8dad09528e
# use space efficient utility from base image

RUN --mount=type=cache,target=/var/cache/apt \
    echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" > /etc/apt/sources.list.d/deadsnakes-ppa.list &&\
    /usr/lib/apt/apt-helper download-file 'https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf23c5a6cf475977595c89f51ba6932366a755776' /etc/apt/trusted.gpg.d/deadsnakes.asc

# install any system dependencies
COPY docker/dependencies.txt /tmp/dependencies.txt
RUN --mount=type=cache,target=/var/cache/apt \
    /root/docker-apt-install.sh /tmp/dependencies.txt

#################################################
#
# Create node image.
#
FROM node:22 AS node-builder
COPY --from=base-python /root/docker-apt-install.sh /root/docker-apt-install.sh

RUN /root/docker-apt-install.sh rsync

WORKDIR /usr/src/app
RUN mkdir -p ./assets

# copy just what npm ci needs
COPY .gitignore biome.json package-lock.json package.json tsconfig.json ./
RUN --mount=type=cache,target=/usr/src/app/.npm \
    npm set cache /usr/src/app/.npm && \
    npm ci

# just copy in the files `npm run build` needs
COPY vite.config.mjs ./
COPY assets/src ./assets/src
COPY templates ./templates
RUN --mount=type=cache,target=./npm npm run build

##################################################
#
# Build image
#
# Ok, now we have local base image with python and our system dependencies on.
# We'll use this as the base for our builder image, where we'll build and
# install any python packages needed.
#
# We use a separate, disposable build image to avoid carrying the build
# dependencies into the production image.
FROM base-python as builder

# Install any system build dependencies
COPY docker/build-dependencies.txt /tmp/build-dependencies.txt
RUN --mount=type=cache,target=/var/cache/apt \
    /root/docker-apt-install.sh /tmp/build-dependencies.txt

# Install everything in venv for isolation from system python libraries
RUN python3.12 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv/ PATH="/opt/venv/bin:$PATH"

# The cache mount means a) /root/.cache is not in the image, and b) it's preserved
# between docker builds locally, for faster dev rebuild.
COPY requirements.prod.txt /tmp/requirements.prod.txt

# DL3042: using cache mount instead
# DL3013: we always want latest pip/setuptools/wheel, at least for now
# hadolint ignore=DL3042,DL3013
RUN --mount=type=cache,target=/root/.cache \
    python -m pip install -U pip setuptools wheel && \
    python -m pip install --require-hashes --requirement /tmp/requirements.prod.txt


##################################################
#
# Base project image
#
# Ok, we've built everything we need, build an image with all dependencies but
# no code.
#
# Not including the code at this stage has two benefits:
#
# 1) this image only rebuilds when the handlful of files needed to build opencodelists-base
#    changes. If we do `COPY . /app` now, this will rebuild when *any* file changes.
#
# 2) Ensures we *have* to mount the volume for dev image, as there's no embedded
#    version of the code. Otherwise, we could end up accidentally using the
#    version of the code included when the prod image was built.
FROM base-python as opencodelists-base

# copy venv over from builder image. These will have root:root ownership, but
# are readable by all.
COPY --from=builder /opt/venv /opt/venv

RUN mkdir -p /app
WORKDIR /app

# copy node assets over from node-builder image. These will have root:root ownership, but
# are readable by all.
COPY --from=node-builder /usr/src/app/assets/dist /opt/assets

# Asset and staticfile management
#
# We support two dev environment side-by-side. Docker-based, which is the same
# everywhere, and the same as production. And host-based, which can mean OSX
# or some version linux. Windows not supported, currently
#
# Both dev envs have tooling and config to generate js assets and to run
# django's collectstatic. In the host-based tooling, these are written to
# ./assets/dist and ./staticfiles respectively. When we run the dev image, we
# mount the host directory in, which means that by default, the tooling when
# run inside the dev container would write to those same directories, which
# would overwrite the host's files.
#
# This is problem because if the host is OSX, this will break some npm stuff,
# and the collectfiles will race between the host-based and docker-based to
# write those files. There can also be file permissions issues.
#
# To solve this we parameterize those locations via BUILT_ASSETS and
# STATIC_ROOT env vars, and within the docker image set them to paths outside
# of /app, so they do not clash in anyway with the host-based generated files.
#
# We do this in both dev and prod docker images. The ./staticfiles and
# ./assets/dist directories are excluded in .dockerignore, so the prod image
# only ever has the files it builds. As the app dir is mounted in the dev
# image, it can see them, but the use of these separate directories means it
# will never use them.
ENV VIRTUAL_ENV=/opt/venv/  \
    PATH="/opt/venv/bin:$PATH"  \
    PYTHONPATH=/app  \
    BUILT_ASSETS=/opt/assets  \
    STATIC_ROOT=/opt/staticfiles \
    DJANGO_SETTINGS_MODULE="opencodelists.settings" \
    OTEL_SERVICE_NAME="opencodelists"


##################################################
#
# Production image
#
# Copy code in, add proper metadata
FROM opencodelists-base as opencodelists-prod

# Dokku is using port 7000 rather than the default 5000
# We need to expose it here so that the dokku checks will use the correct port
EXPOSE 7000

# Adjust this metadata to fit project. Note that the base-docker image does set
# some basic metadata.
LABEL org.opencontainers.image.title="opencodelists" \
      org.opencontainers.image.description="OpenCodelists" \
      org.opencontainers.image.source="https://github.com/opensafely-core/opencodelists"

# copy application code
COPY . /app

# collect static files
RUN TRUD_API_KEY=dummy-key SECRET_KEY=dummy-key \
    python /app/manage.py collectstatic --no-input

# We set command rather than entrypoint, to make it easier to run different
# things from the cli
CMD ["gunicorn", "--config", "/app/deploy/gunicorn/conf.py", "opencodelists.wsgi"]

# finally, tag with build information. These will change regularly, therefore
# we do them as the last action.
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.created=$BUILD_DATE
ARG GITREF=unknown
LABEL org.opencontainers.image.revision=$GITREF

ARG USERID=10003
ARG GROUPID=10003
USER ${USERID}:${GROUPID}

##################################################
#
# Dev image
#
# Now we build a dev image from our output-explorer-base image. This is basically
# installing dev dependencies and changing the entrypoint
#
FROM opencodelists-base as opencodelists-dev

# install development requirements
COPY requirements.dev.txt /tmp/requirements.dev.txt
# using cache mount instead
# hadolint ignore=DL3042
RUN --mount=type=cache,target=/root/.cache \
    python -m pip install --require-hashes --requirement /tmp/requirements.dev.txt

# Install playwright chromium dependencies. This needs to be done AFTER
# playwright is pip-installed
RUN playwright install-deps chromium

# Override ENTRYPOINT rather than CMD so we can pass arbitrary commands to the entrypoint script
ENTRYPOINT ["/app/docker/entrypoints/dev.sh"]

# Run as non root user. Required when building image.
ARG USERID
ARG GROUPID
USER ${USERID}:${GROUPID}
