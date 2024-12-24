#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 <path_to_env_directory> <use_case> <APP_PORT> <WEBSITE_ID>"
  echo "Use cases:"
  echo "  nodejs          - Only update APP_PORT, WEBSITE_ID, and PORT"
  echo "  nodejs_mysql    - Update APP_PORT, WEBSITE_ID, PORT, and MYSQL_HOST"
  echo "  nodejs_mysql_redis - Update all variables (APP_PORT, WEBSITE_ID, PORT, MYSQL_HOST, REDIS_HOST)"
  exit 1
}

# Check if sufficient arguments are provided
if [ $# -lt 4 ]; then
  usage
fi

# Arguments
ENV_DIR=$1
USE_CASE=$2
APP_PORT=$3
WEBSITE_ID=$4
ENV_FILE="$ENV_DIR/.env"

# Default container port for the application
PORT=3000  

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE does not exist."
  exit 1
fi

# Backup the existing .env file
cp "$ENV_FILE" "${ENV_FILE}.bak"

# Remove specific keys
remove_keys() {
  local keys=("$@")
  for key in "${keys[@]}"; do
    sed -i "/^$key=/d" "$ENV_FILE"
  done
}

# Add variables
add_variables() {
  local variables=("$@")
  for var in "${variables[@]}"; do
    echo "$var" >> "$ENV_FILE"
  done
}

# Use case logic
case $USE_CASE in
  nodejs)
    echo "Updating for Node.js only..."
    remove_keys APP_PORT WEBSITE_ID PORT
    add_variables \
      "APP_PORT=$APP_PORT" \
      "WEBSITE_ID=$WEBSITE_ID" \
      "PORT=$PORT"
    ;;
  nodejs_mysql)
    echo "Updating for Node.js with MySQL..."
    remove_keys APP_PORT WEBSITE_ID PORT MYSQL_HOST
    add_variables \
      "APP_PORT=$APP_PORT" \
      "WEBSITE_ID=$WEBSITE_ID" \
      "PORT=$PORT" \
      "MYSQL_HOST=mysql"
    ;;
  nodejs_mysql_redis)
    echo "Updating for Node.js with MySQL and Redis..."
    remove_keys APP_PORT WEBSITE_ID PORT MYSQL_HOST REDIS_HOST
    add_variables \
      "APP_PORT=$APP_PORT" \
      "WEBSITE_ID=$WEBSITE_ID" \
      "PORT=$PORT" \
      "MYSQL_HOST=mysql" \
      "REDIS_HOST=redis"
    ;;
  *)
    echo "Invalid use case."
    usage
    ;;
esac

echo "Environment file updated successfully."
