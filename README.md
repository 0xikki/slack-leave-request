# Slack Leave Request System

A Slack-integrated leave request system that allows users to submit and manage leave requests directly through Slack.

## Features

- Submit leave requests using `/timeoff` command in Slack
- Interactive modal for submitting leave request details:
  - Leave type selection (Vacation, Sick Leave, Personal)
  - Start and end date selection
  - Reason for leave
- Admin approval workflow with:
  - Instant notifications in admin channel
  - One-click approve/reject buttons
  - Rejection reason collection via modal
- Automatic notifications for:
  - Request submission confirmation
  - Request approval/rejection status
- Secure HTTPS endpoints with Slack request verification
- Modern Slack Block Kit UI with interactive components

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
# Edit .env with your Slack tokens and configuration:
# SLACK_BOT_TOKEN=xoxb-your-token
# SLACK_SIGNING_SECRET=your-signing-secret
# SLACK_ADMIN_CHANNEL=leave-requests
```

4. Run the development server:
```bash
python -m flask --app src.app run --debug
```

5. Set up your Slack App:
   - Create a new Slack App at https://api.slack.com/apps
   - Add the following Slash Command:
     - Command: `/timeoff`
     - Request URL: `https://your-domain/slack/commands`
   - Enable Interactivity:
     - Request URL: `https://your-domain/slack/interactivity`
   - Add Bot Token Scopes:
     - `chat:write`
     - `commands`
     - `users:read`
   - Install the app to your workspace

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
- Request timestamp validation
- Signature verification for all Slack requests

## Development

- Written in Python with type hints
- Follows PEP8 guidelines
- Comprehensive test suite with pytest
- Error handling and logging
- Modular design with separation of concerns

## License

MIT License 