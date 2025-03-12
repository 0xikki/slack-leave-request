# Deployment script for Slack Leave Request System using web setup
param(
    [Parameter(Mandatory=$true)]
    [string]$VultrIP,
    [string]$Domain = "slack-leave.$VultrIP.nip.io"
)

# Configuration
$AppPath = "/var/www/slack-leave-system"
$EnvFile = ".env"

Write-Host "Starting web-based deployment to $Domain..."

# 1. Create deployment package
Write-Host "Creating deployment package..."
Compress-Archive -Path "src/*", "requirements.txt", "gunicorn.conf.py", "nginx.conf" -DestinationPath "deploy.zip" -Force

# 2. Create setup script
$setupScript = @"
#!/bin/bash
# Update system
apt-get update
apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx ufw

# Configure firewall
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

# Create application directory
mkdir -p $AppPath
cd $AppPath

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Nginx
cp nginx.conf /etc/nginx/nginx.conf
sed -i 's/your_domain.com/$Domain/g' /etc/nginx/nginx.conf
systemctl restart nginx

# Set up SSL
certbot --nginx -d $Domain --non-interactive --agree-tos --email admin@$Domain

# Create systemd service
cat > /etc/systemd/system/slack-leave-system.service << 'EOL'
[Unit]
Description=Slack Leave Request System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$AppPath
Environment="PATH=$AppPath/venv/bin"
ExecStart=$AppPath/venv/bin/gunicorn -c gunicorn.conf.py src.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Start services
systemctl daemon-reload
systemctl enable slack-leave-system
systemctl start slack-leave-system

# Set up logs
mkdir -p $AppPath/logs
chown -R www-data:www-data $AppPath
"@

Set-Content -Path "setup.sh" -Value $setupScript

Write-Host "Deployment package and setup script created!"
Write-Host "Please follow these steps to complete deployment:"
Write-Host "1. Log into your Vultr instance through the web console at https://my.vultr.com/"
Write-Host "2. Upload deploy.zip and setup.sh to the server"
Write-Host "3. Run: chmod +x setup.sh && ./setup.sh"
Write-Host ""
Write-Host "After deployment completes, your application will be available at:"
Write-Host "https://$Domain" 