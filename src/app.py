import os
import json
import hmac
import hashlib
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
from logging.config import dictConfig
from pythonjsonlogger import jsonlogger
from slack_sdk.signature import SignatureVerifier
from functools import wraps
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack.slack_commands import SlackCommandsHandler
from slack.slack_actions import SlackActionsHandler

# Load environment variables
load_dotenv()

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {
        'json': {
            '()': jsonlogger.JsonFormatter,
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack client
slack_token = os.getenv("SLACK_BOT_TOKEN")
if not slack_token:
    raise ValueError("SLACK_BOT_TOKEN environment variable is not set")

slack_client = WebClient(token=slack_token)
actions_handler = SlackActionsHandler(slack_client)
commands_handler = SlackCommandsHandler(slack_client)

def verify_slack_request(f):
    """Decorator to verify that the request is coming from Slack."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        timestamp = request.headers.get('X-Slack-Request-Timestamp')
        signature = request.headers.get('X-Slack-Signature')

        if not timestamp or not signature:
            return jsonify({"ok": False, "error": "Invalid request signature"}), 401

        # Check if the timestamp is too old
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return jsonify({"ok": False, "error": "Request too old"}), 401

        # Get request body as string
        request_body = request.get_data().decode('utf-8')

        # Create signature base string
        sig_basestring = f"v0:{timestamp}:{request_body}"

        # Calculate signature
        calculated_signature = 'v0=' + hmac.new(
            os.environ.get('SLACK_SIGNING_SECRET', '').encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures using constant time comparison
        if not hmac.compare_digest(calculated_signature, signature):
            return jsonify({"ok": False, "error": "Invalid request signature"}), 401

        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def verify_slack_requests():
    """Verify Slack requests before processing."""
    if request.endpoint in ['slack_commands', 'slack_interactivity', 'slack_actions']:
        timestamp = request.headers.get('X-Slack-Request-Timestamp')
        signature = request.headers.get('X-Slack-Signature')

        if not timestamp or not signature:
            app.logger.warning("Invalid request signature")
            return jsonify({"ok": False, "error": "Invalid request signature"}), 401

        # Check if the timestamp is too old
        if abs(time.time() - int(timestamp)) > 60 * 5:
            app.logger.warning("Request too old")
            return jsonify({"ok": False, "error": "Request too old"}), 401

        # Get request body as string
        request_body = request.get_data().decode('utf-8')

        # Create signature base string
        sig_basestring = f"v0:{timestamp}:{request_body}"

        # Calculate signature
        calculated_signature = 'v0=' + hmac.new(
            os.environ.get('SLACK_SIGNING_SECRET', '').encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures using constant time comparison
        if not hmac.compare_digest(calculated_signature, signature):
            app.logger.warning("Invalid request signature")
            return jsonify({"ok": False, "error": "Invalid request signature"}), 401

@app.route('/slack/commands', methods=['POST'])
def slack_commands():
    """Handle Slack slash commands."""
    try:
        return commands_handler.handle_command(request.form)
    except Exception as e:
        app.logger.error(f"Error handling command: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/slack/interactivity', methods=['POST'])
def slack_interactivity():
    """Handle Slack interactive components."""
    try:
        form_data = dict(request.form)
        payload = json.loads(form_data['payload'])
        
        if payload['type'] == 'view_submission':
            response = actions_handler.handle_action(payload)
            return jsonify(response)
            
        return jsonify({"ok": False, "error": "Unsupported interaction type"}), 400
        
    except (KeyError, json.JSONDecodeError) as e:
        app.logger.error(f"Error processing interactive payload: {str(e)}")
        return jsonify({"ok": False, "error": "Invalid payload"}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"ok": False, "error": "Internal server error"}), 500

@app.route("/slack/actions", methods=["POST"])
@verify_slack_request
def handle_actions():
    """Handle Slack interactive actions (button clicks and modal submissions)."""
    try:
        # Parse the request payload
        payload = json.loads(request.form["payload"])
        return actions_handler.handle_action(payload)
        
    except Exception as e:
        app.logger.error(f"Error handling action: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events and interactions"""
    data = request.json
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})
    
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 