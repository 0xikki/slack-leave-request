# Slack Leave Request System

A Slack-integrated leave request system that allows users to submit and manage leave requests directly through Slack.

## Features

- Submit leave requests using `/leave` command in Slack
- Interactive modal for leave request details
- Admin approval workflow
- Automatic notifications
- Secure HTTPS endpoints
- Full Slack Block Kit UI

## Tech Stack

- Python 3.9+
- Flask for web server
- Slack SDK for Slack integration
- Gunicorn for production server
- Nginx for reverse proxy
- SSL/TLS encryption with Let's Encrypt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/slack-leave-request.git
cd slack-leave-request
```

2. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Slack tokens and configuration
```

4. Run the development server:
```bash
python src/app.py
```

## Deployment

The system includes deployment scripts for Vultr hosting:

1. Run the deployment script:
```powershell
.\deploy_web.ps1 -VultrIP "YOUR_SERVER_IP"
```

2. Follow the on-screen instructions to complete deployment

## Security

- All endpoints require Slack request verification
- HTTPS-only communication
- Environment-based configuration
- Secure credential storage

## License

MIT License 