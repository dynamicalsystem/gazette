#!/bin/bash
# Quick deployment script for gazette

# Create deployment directory
DEPLOY_DIR="$HOME/.local/opt/dynamicalsystem.gazette"
echo "Creating deployment directory: $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Download docker-compose.yml
echo "Downloading docker-compose.yml..."
curl -H 'Cache-Control: no-cache' -O https://raw.githubusercontent.com/dynamicalsystem/gazette/main/docker-compose.yml

# Create necessary directories
echo "Creating directories..."
mkdir -p ~/.local/share/dynamicalsystem/{config,data}

# Set environment variables
export DYNAMICAL_SYSTEM_FOLDER=${DYNAMICAL_SYSTEM_FOLDER:~/.local/share/dynamicalsystem}
export ENV=${ENVIRONMENT:-$(whoami)}
export HOST_FOLDER=${HOST_FOLDER:-~/.local/share}
export SUBFOLDER=${SUBFOLDER:-dynamicalsystem}
export TZ=${TZ:-Europe/London}

# Set port based on environment
if [ "$ENVIRONMENT" = "test" ]; then
    export SIGNAL_PORT=8110
else
    export SIGNAL_PORT=8010
fi

# Set user ID for container
export CONTAINER_UID=$(id -u)
export CONTAINER_GID=$(id -g)

echo "Environment settings:"
echo "  ENV: $ENV"
echo "  SIGNAL_PORT: $SIGNAL_PORT"
echo "  CONTAINER_UID: $CONTAINER_UID"
echo "  CONTAINER_GID: $CONTAINER_GID"
echo "  HOST_FOLDER: $HOST_FOLDER"
echo "  SUBFOLDER: $SUBFOLDER"
echo "  TZ: $TZ"

# Create .env file for docker-compose
echo "Creating .env file..."
cat > .env << EOF
ENV=${ENVIRONMENT:-$(whoami)}
DYNAMICAL_SYSTEM_FOLDER=${DYNAMICAL_SYSTEM_FOLDER}
HOST_FOLDER=${HOST_FOLDER}
SUBFOLDER=${SUBFOLDER}
TZ=${TZ}
SIGNAL_PORT=${SIGNAL_PORT}
CONTAINER_UID=${CONTAINER_UID}
CONTAINER_GID=${CONTAINER_GID}
EOF

echo "Created .env file with:"
cat .env

# Deploy containers
echo "Deploying containers..."
# Start signal service
docker compose up -d
# Create gazette container without starting it
docker compose --profile scheduled create gazette

echo "Deployment complete!"
echo "Note: Don't forget to add your configuration files to ${DYNAMICAL_SYSTEM_FOLDER}config/"
echo ""
echo "Next steps:"
echo "1. cd $DEPLOY_DIR"
echo "2. Run \`docker compose up -d\` to bring up gazette"