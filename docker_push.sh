#!/bin/bash

# Function to print usage
print_usage() {
  echo "Usage: $0 [-i image]"
  echo "  -i image              Docker krasaee/alethic-ism-api:latest"
}

# Parse command line arguments
while getopts 'i:' flag; do
  case "${flag}" in
    i) IMAGE="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

echo "pushing docker image"
docker push $IMAGE
