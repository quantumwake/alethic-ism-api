#!/bin/bash

# Function to print usage
print_usage() {
  echo "Usage: $0 [-t image] [-p architecture]"
  echo "  -i image           Docker image krasaee/alethic-ism-api:latest"
  echo "  -p platform        Target platform architecture (linux/amd64, linux/arm64, ...)"
}

# Default values
ARCH="linux/amd64"

# Parse command line arguments
while getopts 'i:a:' flag; do
  case "${flag}" in
    i) IMAGE="${OPTARG}" ;;
    p) ARCH="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

# Check if ARCH is set, if not default to linux/amd64
if [ -z "$ARCH" ]; then
  ARCH="linux/amd64"
  # TODO: Check operating system and set ARCH accordingly, e.g., ARCH="linux/arm64"
fi

## Display arguments
echo "platform: $ARCH"
echo "platform image: $IMAGE"

# Build the Docker image which creates the package
docker build --progress=plain \
  --platform "$ARCH" -t "$IMAGE" \
  --no-cache .
