#!/bin/bash
# Quick deployment script for gazette

# Download docker-compose.yml
echo "Downloading docker-compose.yml..."
curl -O https://raw.githubusercontent.com/dynamicalsystem/gazette/main/docker-compose.yml

# Create necessary directories
echo "Creating directories..."
mkdir -p ~/.local/share/dynamicalsystem/{config,data}

# Set environment variables
export DYNAMICALSYSTEM_ENVIRONMENT=${DYNAMICALSYSTEM_ENVIRONMENT:-prod}
export HOST_FOLDER=${HOST_FOLDER:-~/.local/share}
export TZ=${TZ:-Europe/London}

echo "Environment settings:"
echo "  DYNAMICALSYSTEM_ENVIRONMENT: $DYNAMICALSYSTEM_ENVIRONMENT"
echo "  HOST_FOLDER: $HOST_FOLDER"
echo "  TZ: $TZ"

# Deploy containers
echo "Deploying containers..."
docker-compose up -d

echo "Deployment complete!"
echo "Note: Don't forget to add your configuration files to $HOST_FOLDER/dynamicalsystem/config/"