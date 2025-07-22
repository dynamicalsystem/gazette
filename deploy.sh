#!/bin/bash
# Quick deployment script for gazette

# Download docker-compose.yml
echo "Downloading docker-compose.yml..."
curl -H 'Cache-Control: no-cache' -O https://raw.githubusercontent.com/dynamicalsystem/gazette/main/docker-compose.yml

# Create necessary directories
# Put config on NAS...
# echo "username=<USERANME>
# password=<PASSWORD>
# domain=WORKGROUP" | sudo tee -a /etc/samba/credentials
# sudo chmod 600 /etc/samba/credentials
# sudo mkdir -p /mnt/home
# Following line assumes docker container is in gid 1000
# sudo mount -t cifs //<NAS>.local/home /mnt/home -o username=<USERNAME>
# echo "//<NAS>.local/home /mnt/home cifs credentials=/etc/samba/credentials,uid=1000,gid=1000,iocharset=utf8,file_mode=0777,dir_mode=0777,noperm 0 0" | sudo tee -a /etc/fstab

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

# Create .env file for docker-compose
echo "Creating .env file..."
cat > .env << EOF
ENV=${ENV}
HOST_FOLDER=${HOST_FOLDER}
SUBFOLDER=${SUBFOLDER}
TZ=${TZ}
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
echo "Note: Don't forget to add your configuration files to $HOST_FOLDER/dynamicalsystem/config/"