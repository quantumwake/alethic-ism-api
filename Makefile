# Makefile
.PHONY: build push deploy all

# Determine VERSION:
#  - if we're on a tag: use that tag name
#  - otherwise fall back to short SHA
VERSION := $(shell \
  if git describe --exact-match --tags >/dev/null 2>&1; then \
    git describe --exact-match --tags; \
  else \
    git rev-parse --short HEAD; \
  fi \
)

IMAGE_BASE ?= "krasaee/alethic-ism-api"

# Default image name - can be overridden with make IMAGE=your-image-name
IMAGE ?= $(IMAGE_BASE):$(VERSION)

# Ensure scripts are executable
init:
	chmod +x docker_build.sh docker_push.sh docker_deploy.sh

# Build the Docker image using buildpacks
build:
	sh docker_build.sh -i $(IMAGE)

# Push the Docker image to registry
push:
	sh docker_push.sh -i $(IMAGE)

# Deploy the application to kubernetes using the k8s/deployment.yaml as a template.
deploy:
	sh docker_deploy.sh -i $(IMAGE)

# Build, push and deploy
all: build push deploy

# Clean up old images and containers (optional)
clean:
	@docker system prune -f