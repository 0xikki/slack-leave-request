# Deployment script for Slack Leave Request System
param(
    [Parameter(Mandatory=$true)]
    [string]$VultrIP,
    
    [Parameter(Mandatory=$true)]
    [string]$SSHKeyPath,
    
    [Parameter(Mandatory=$true)]
    [string]$Domain
)

# Configuration
$RemoteUser = "root"
$AppPath = "/var/www/slack-leave-system"
$EnvFile = ".env"

Write-Host "Starting deployment to Vultr server at $VultrIP..."

# 1. Test SSH connection
Write-Host "Testing SSH connection..."
ssh -i $SSHKeyPath -o StrictHostKeyChecking=no "${RemoteUser}@${VultrIP}" "echo 'SSH connection successful'"

# 2. Install system dependencies
Write-Host "Installing system dependencies..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    apt-get update
    apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx ufw
"@

# 3. Configure firewall
Write-Host "Configuring firewall..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    ufw allow 'Nginx Full'
    ufw allow OpenSSH
    ufw --force enable
"@

# 4. Create application directory
Write-Host "Creating application directory..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    mkdir -p $AppPath
    chown -R www-data:www-data $AppPath
"@

# 5. Copy application files
Write-Host "Copying application files..."
scp -i $SSHKeyPath -r ./* "${RemoteUser}@${VultrIP}:$AppPath/"

# 6. Set up Python virtual environment
Write-Host "Setting up Python virtual environment..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    cd $AppPath
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
"@

# 7. Configure Nginx
Write-Host "Configuring Nginx..."
$NginxConfig = Get-Content nginx.conf
$NginxConfig = $NginxConfig -replace 'your_domain.com', $Domain
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    echo '$NginxConfig' > /etc/nginx/nginx.conf
    systemctl restart nginx
"@

# 8. Set up SSL certificate
Write-Host "Setting up SSL certificate..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    certbot --nginx -d $Domain --non-interactive --agree-tos --email admin@$Domain
"@

# 9. Configure systemd service
Write-Host "Configuring systemd service..."
scp -i $SSHKeyPath slack-leave-system.service "${RemoteUser}@${VultrIP}:/etc/systemd/system/"
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    systemctl daemon-reload
    systemctl enable slack-leave-system
    systemctl start slack-leave-system
"@

# 10. Create logs directory
Write-Host "Creating logs directory..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    mkdir -p $AppPath/logs
    chown -R www-data:www-data $AppPath/logs
"@

# 11. Final checks
Write-Host "Performing final checks..."
ssh -i $SSHKeyPath "${RemoteUser}@${VultrIP}" @"
    systemctl status nginx
    systemctl status slack-leave-system
    curl -k https://localhost
"@

Write-Host "Deployment completed successfully!"
Write-Host "Please update your Slack App configuration with the new URL: https://$Domain" 