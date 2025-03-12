#!/bin/bash
# Update system
apt-get update
apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx ufw

# Configure firewall
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

# Create application directory
mkdir -p /var/www/slack-leave-system
cd /var/www/slack-leave-system

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Nginx
cp nginx.conf /etc/nginx/nginx.conf
sed -i 's/your_domain.com/slack-leave.66.42.93.121.nip.io/g' /etc/nginx/nginx.conf
systemctl restart nginx

# Set up SSL
certbot --nginx -d slack-leave.66.42.93.121.nip.io --non-interactive --agree-tos --email admin@slack-leave.66.42.93.121.nip.io

# Create systemd service
cat > /etc/systemd/system/slack-leave-system.service << 'EOL'
[Unit]
Description=Slack Leave Request System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/slack-leave-system
Environment="PATH=/var/www/slack-leave-system/venv/bin"
ExecStart=/var/www/slack-leave-system/venv/bin/gunicorn -c gunicorn.conf.py src.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Start services
systemctl daemon-reload
systemctl enable slack-leave-system
systemctl start slack-leave-system

# Set up logs
mkdir -p /var/www/slack-leave-system/logs
chown -R www-data:www-data /var/www/slack-leave-system
