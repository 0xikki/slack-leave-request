#!/bin/bash

# Create a temporary directory
mkdir -p /tmp/deploy
cd /tmp/deploy

# Download files using base64 encoded content
echo "Downloading deployment files..."

# deploy.zip content
cat > deploy.zip << 'EOL'
$(base64 deploy.zip)
EOL

# setup.sh content
cat > setup.sh << 'EOL'
$(base64 setup.sh)
EOL

# Decode files
base64 -d deploy.zip > /root/deploy/deploy.zip
base64 -d setup.sh > /root/deploy/setup.sh

# Clean up
cd /root/deploy
rm -rf /tmp/deploy

# Make setup script executable
chmod +x setup.sh

echo "Files downloaded successfully!" 