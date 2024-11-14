#!/bin/bash

# Check if both file paths are provided as arguments
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: ./post_code_with_queries.sh <path_to_code_file> <path_to_queries_file>"
  exit 1
fi

# Read the code content from the specified code file
code_content=$(<"$1")

# Read the queries JSON content from the specified queries file
queries=$(<"$2")

# Define the JSON payload with code_content and queries
json_payload=$(jq -n \
  --arg code_content "$code_content" \
  --argjson queries "$queries" \
  '{code_content: $code_content, queries: $queries}')

# Send the JSON payload to the FastAPI endpoint using curl
curl -X POST "http://localhost:8000/validate/python" \
     -H "Content-Type: application/json" \
     -d "$json_payload"