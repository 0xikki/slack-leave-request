"""
Flask application for handling Slack interactions.
"""

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
from src.slack.slack_commands import SlackCommandsHandler
from src.slack.slack_actions import SlackActionsHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)  # Force override any existing env vars

# Debug environment variables
logger.debug("Environment variables at startup:")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f".env file location: {os.path.abspath('.env')}")
logger.debug(f"SLACK_ADMIN_USER_IDS raw: {os.getenv('SLACK_ADMIN_USER_IDS', 'Not set')}")
logger.debug(f"SLACK_ADMIN_USER_IDS type: {type(os.getenv('SLACK_ADMIN_USER_IDS', 'Not set'))}")
logger.debug(f"SLACK_BOT_TOKEN: {'Set' if os.getenv('SLACK_BOT_TOKEN') else 'Not set'}")
logger.debug(f"SLACK_SIGNING_SECRET: {'Set' if os.getenv('SLACK_SIGNING_SECRET') else 'Not set'}")

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

# Initialize Slack client and handlers
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
slack_commands = SlackCommandsHandler(slack_client)
slack_actions = SlackActionsHandler(slack_client)
signature_verifier = SignatureVerifier(os.environ.get("SLACK_SIGNING_SECRET", "test_signing_secret"))

def verify_slack_request(f):
    """Decorator to verify Slack requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
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

@app.route("/slack/commands", methods=["POST"])
@verify_slack_request
def handle_command():
    """Handle Slack slash commands."""
    try:
        response = slack_commands.handle_command(request.form)
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "response_type": "ephemeral",
            "text": "An error occurred"
        }), 200

@app.route("/slack/interactivity", methods=["POST"])
def handle_interaction():
    """Handle Slack interactive components."""
    try:
        # Verify request signature
        if not verify_slack_request(request):
            logger.error("Invalid request signature")
            return jsonify({"error": "Invalid request"}), 401

        # Parse payload
        payload = json.loads(request.form["payload"])
        interaction_type = payload.get("type")

        if interaction_type == "view_submission":
            # Handle modal submission
            try:
                response = slack_actions.handle_view_submission(payload)
                if not response:
                    # For successful submissions, return an empty object
                    return jsonify({}), 200
                if response.get("response_action") == "errors":
                    # For validation errors, return the errors
                    return jsonify(response), 200
                # For any other response, return empty object
                return jsonify({}), 200
            except Exception as e:
                logger.error(f"Error in view submission: {str(e)}")
                # On error, return empty object to close modal
                return jsonify({}), 200

        elif interaction_type == "block_actions":
            # Handle button clicks and other block actions
            response = slack_actions.handle_action(payload)
            if response.get("response_action") == "clear":
                return jsonify({}), 200
            return jsonify(response), 200

        # For any other interaction type, return empty object
        return jsonify({}), 200

    except Exception as e:
        logger.error(f"Error handling interaction: {str(e)}")
        # On error, return empty object
        return jsonify({}), 200

@app.route("/slack/events", methods=["POST"])
@verify_slack_request
def slack_events():
    """Handle Slack events and interactions"""
    data = request.json
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})
    
    return jsonify({"ok": True})

@app.route("/slack/actions", methods=["POST"])
def handle_actions():
    """Handle Slack actions - mirrors the interactivity endpoint."""
    return handle_interaction()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 