#!/bin/bash
# Quick deployment script for gazette

# Download docker-compose.yml
echo "Downloading docker-compose.yml..."
curl -O https://raw.githubusercontent.com/dynamicalsystem/gazette/main/docker-compose.yml

# Create necessary directories
echo "Creating directories..."
mkdir -p ~/.local/share/dynamicalsystem/{config,data}

# Set environment variables
export ENV=${ENV:-prod}
export HOST_FOLDER=${HOST_FOLDER:-~/.local/share}
export SUBFOLDER=${SUBFOLDER:-dynamicalsystem}
export TZ=${TZ:-Europe/London}

echo "Environment settings:"
echo "  ENV: $ENV"
echo "  HOST_FOLDER: $HOST_FOLDER"
echo "  SUBFOLDER: $SUBFOLDER"
echo "  TZ: $TZ"

# Deploy containers
echo "Deploying containers..."
# Start signal service
docker compose up -d
# Create gazette container without starting it
docker compose --profile scheduled create gazette

echo "Deployment complete!"
echo "Note: Don't forget to add your configuration files to $HOST_FOLDER/dynamicalsystem/config/"