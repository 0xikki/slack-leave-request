import os
import json
import hmac
import hashlib
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src.slack_commands import SlackCommandHandler
from src.slack_actions import SlackActionsHandler
import logging
from logging.config import dictConfig
from pythonjsonlogger import jsonlogger
from slack_sdk.signature import SignatureVerifier
from functools import wraps

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
slack_handler = SlackCommandHandler()
slack_actions_handler = SlackActionsHandler()

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
    form_data = dict(request.form)
    command = form_data.get('command')
    user_id = form_data.get('user_id')
    trigger_id = form_data.get('trigger_id')
    
    if command != '/leave':
        return jsonify({"ok": False, "error": "Invalid command"}), 400
        
    response = slack_handler.handle_leave_command(user_id=user_id, trigger_id=trigger_id)
    
    if not response.get('ok'):
        return jsonify(response), 400
        
    return jsonify(response)

@app.route('/slack/interactivity', methods=['POST'])
def slack_interactivity():
    """Handle Slack interactive components."""
    try:
        form_data = dict(request.form)
        payload = json.loads(form_data['payload'])
        
        if payload['type'] == 'view_submission':
            response = slack_handler.handle_modal_submission(payload)
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
        
        # Handle different types of actions
        if payload.get("type") == "block_actions":
            # Handle button clicks (approve/deny)
            response = slack_actions_handler.handle_action(payload)
        elif payload.get("type") == "view_submission":
            # Handle modal submissions (denial reason)
            response = slack_actions_handler.handle_denial_submission(payload)
        else:
            response = {"ok": False, "error": "Unsupported action type"}
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error handling action: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 