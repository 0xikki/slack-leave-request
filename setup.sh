#!/bin/bash
# Update system and install dependencies
apt-get update
apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Configure firewall
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

# Create application directory and copy files
mkdir -p /var/www/slack-leave-system/src
mkdir -p /var/www/slack-leave-system/src/slack
mkdir -p /var/log/slack-leave-system

# Copy source files
cp -r /root/slack-leave-request/src/*.py /var/www/slack-leave-system/src/
cp -r /root/slack-leave-request/src/slack/*.py /var/www/slack-leave-system/src/slack/
cp /root/slack-leave-request/requirements.txt /var/www/slack-leave-system/
cp /root/slack-leave-request/setup.py /var/www/slack-leave-system/
cp /root/slack-leave-request/.env /var/www/slack-leave-system/
cp /root/slack-leave-request/nginx.conf /etc/nginx/sites-available/slack-leave-system
cp /root/slack-leave-request/gunicorn.conf.py /var/www/slack-leave-system/

# Set up Python virtual environment
cd /var/www/slack-leave-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .  # Install our package in development mode

# Configure Nginx
ln -sf /etc/nginx/sites-available/slack-leave-system /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Set up SSL
certbot --nginx -d slack-leave.66.42.93.121.nip.io --non-interactive --agree-tos --email admin@example.com

# Create systemd service
cat > /etc/systemd/system/slack-leave-system.service << EOL
[Unit]
Description=Slack Leave Request System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/slack-leave-system
Environment="PATH=/var/www/slack-leave-system/venv/bin"
EnvironmentFile=/var/www/slack-leave-system/.env
ExecStart=/var/www/slack-leave-system/venv/bin/gunicorn -c gunicorn.conf.py src.app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
chown -R www-data:www-data /var/www/slack-leave-system
chown -R www-data:www-data /var/log/slack-leave-system

# Start and enable service
systemctl daemon-reload
systemctl restart slack-leave-system
systemctl enable slack-leave-system
