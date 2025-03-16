import pytest
from flask import Flask
from unittest.mock import patch, Mock
import json
import hmac
import hashlib
import time
from urllib.parse import urlencode

@pytest.fixture
def client():
    from src.app import app
    with app.test_client() as client:
        yield client

@pytest.fixture
def slack_signature():
    def _make_signature(body):
        timestamp = str(int(time.time()))
        sig_basestring = f"v0:{timestamp}:{body}"
        
        # Create signature using test signing secret
        signature = 'v0=' + hmac.new(
            'test_signing_secret'.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Slack-Request-Timestamp': timestamp,
            'X-Slack-Signature': signature,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    return _make_signature

def test_invalid_command(client, slack_signature):
    """Test that invalid commands return an error."""
    data = {
        'command': '/invalid',
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
        response = client.post('/slack/commands', 
                             data=body,  # Send the raw body
                             headers=headers)
        
    assert response.status_code == 200  # Slack expects 200 even for invalid commands
    response_data = json.loads(response.data)
    assert response_data["response_type"] == "ephemeral"
    assert "Invalid command" in response_data["text"]

def test_timeoff_command_success(client, slack_signature):
    """Test successful /timeoff command processing."""
    data = {
        'command': '/timeoff',
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack.slack_commands.SlackCommandsHandler.handle_command') as mock_handler:
        # Command should return ephemeral message
        mock_handler.return_value = {
            "response_type": "ephemeral",
            "text": "Opening leave request form..."
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/commands', 
                                 data=body,
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["response_type"] == "ephemeral"
    assert "Opening leave request form" in response_data["text"]

def test_timeoff_command_error(client, slack_signature):
    """Test that errors in timeoff command processing are handled."""
    data = {
        'command': '/timeoff',
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack.slack_commands.SlackCommandsHandler.handle_command') as mock_handler:
        mock_handler.return_value = {
            "response_type": "ephemeral",
            "text": "An error occurred. Please try again."
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/commands', 
                                 data=body,  # Send the raw body
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["response_type"] == "ephemeral"
    assert "error" in response_data["text"].lower()

def test_view_submission_success(client, slack_signature):
    """Test successful modal submission processing."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U123456"},
        "view": {
            "callback_id": "leave_request_modal",
            "state": {
                "values": {
                    "leave_type": {
                        "leave_type_select": {
                            "selected_option": {
                                "value": "pto"
                            }
                        }
                    },
                    "leave_dates": {
                        "start_date": {
                            "selected_date": "2024-03-15"
                        }
                    },
                    "end_date": {
                        "end_date": {
                            "selected_date": "2024-03-16"
                        }
                    },
                    "leave_reason": {
                        "reason_text": {
                            "value": "Taking a vacation"
                        }
                    },
                    "tasks_to_cover": {
                        "tasks_text": {
                            "value": "All tasks covered"
                        }
                    },
                    "coverage_person": {
                        "coverage_select": {
                            "selected_user": "U654321"
                        }
                    }
                }
            }
        }
    }
    payload_str = json.dumps(payload)
    data = {"payload": payload_str}
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack.slack_actions.SlackActionsHandler.handle_view_submission') as mock_handler:
        # View submission should return empty response for success
        mock_handler.return_value = ""
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/interactivity', 
                                 data=body,
                                 headers=headers)
            
    assert response.status_code == 200
    assert response.data == b""  # Empty response for success

def test_view_submission_validation_error(client, slack_signature):
    """Test validation error handling in modal submission."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U123456"},
        "view": {
            "callback_id": "leave_request_modal",
            "state": {
                "values": {}  # Empty values to trigger validation error
            }
        }
    }
    payload_str = json.dumps(payload)
    data = {"payload": payload_str}
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack.slack_actions.SlackActionsHandler.handle_view_submission') as mock_handler:
        # Return validation errors
        mock_handler.return_value = {
            "response_action": "errors",
            "errors": {
                "leave_type": "Please select a leave type",
                "leave_dates": "Please select start date",
                "end_date": "Please select end date",
                "leave_reason": "Please provide a reason",
                "tasks_to_cover": "Please list tasks to be covered",
                "coverage_person": "Please select who will cover for you"
            }
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/interactivity', 
                                 data=body,
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["response_action"] == "errors"
    assert len(response_data["errors"]) == 6  # All required fields should have errors

def test_view_submission_clear(client, slack_signature):
    """Test clearing all views in modal submission."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U123456"},
        "view": {
            "callback_id": "leave_request_modal",
            "state": {
                "values": {
                    # Valid submission that needs to clear all views
                }
            }
        }
    }
    payload_str = json.dumps(payload)
    data = {"payload": payload_str}
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack.slack_actions.SlackActionsHandler.handle_view_submission') as mock_handler:
        # Return clear action to close all views
        mock_handler.return_value = {
            "response_action": "clear"
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/interactivity', 
                                 data=body,
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["response_action"] == "clear"

def test_invalid_signature(client):
    """Test that requests with invalid signatures are rejected."""
    data = {
        'command': '/timeoff',  # Updated to match actual command
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    headers = {
        'X-Slack-Request-Timestamp': str(int(time.time())),
        'X-Slack-Signature': 'v0=invalid_signature'
    }
    
    with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
        response = client.post('/slack/commands', 
                             data=data, 
                             headers=headers)
        
    assert response.status_code == 401
    response_data = json.loads(response.data)
    assert response_data["error"] == "Invalid request signature" 