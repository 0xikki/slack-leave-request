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
        
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert response_data["error"] == "Invalid command"

def test_valid_leave_command(client, slack_signature):
    """Test that valid /leave commands are processed."""
    data = {
        'command': '/leave',
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack_commands.SlackCommandHandler.handle_leave_command') as mock_handler:
        mock_handler.return_value = {"ok": True}
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/commands', 
                                 data=body,  # Send the raw body
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["ok"] is True

def test_leave_command_error(client, slack_signature):
    """Test that errors in leave command processing are handled."""
    data = {
        'command': '/leave',
        'user_id': 'U123456',
        'trigger_id': 'trigger123'
    }
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack_commands.SlackCommandHandler.handle_leave_command') as mock_handler:
        mock_handler.return_value = {
            "ok": False,
            "error": "Test error message"
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/commands', 
                                 data=body,  # Send the raw body
                                 headers=headers)
            
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert response_data["ok"] is False
    assert response_data["error"] == "Test error message"

def test_modal_submission_success(client, slack_signature):
    """Test successful modal submission processing."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U123456"},
        "view": {
            "state": {
                "values": {
                    "leave_dates": {
                        "start_date": {
                            "selected_date": "2024-03-15"
                        },
                        "end_date": {
                            "selected_date": "2024-03-16"
                        }
                    },
                    "leave_type": {
                        "leave_type_select": {
                            "selected_option": {
                                "value": "pto"
                            }
                        }
                    },
                    "leave_reason": {
                        "reason_text": {
                            "value": "Taking a vacation"
                        }
                    },
                    "tasks_coverage": {
                        "tasks_text": {
                            "value": "All tasks covered"
                        }
                    },
                    "covering_person": {
                        "covering_user_select": {
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
    
    with patch('src.slack_commands.SlackCommandHandler.handle_modal_submission') as mock_handler:
        mock_handler.return_value = {"ok": True}
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/interactivity', 
                                 data=body,  # Send the raw body
                                 headers=headers)
            
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["ok"] is True

def test_modal_submission_error(client, slack_signature):
    """Test error handling in modal submission."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U123456"},
        "view": {
            "state": {
                "values": {}  # Empty values to trigger error
            }
        }
    }
    payload_str = json.dumps(payload)
    data = {"payload": payload_str}
    body = urlencode(data)
    headers = slack_signature(body)
    
    with patch('src.slack_commands.SlackCommandHandler.handle_modal_submission') as mock_handler:
        mock_handler.return_value = {
            "ok": False,
            "error": "Missing required fields"
        }
        with patch.dict('os.environ', {'SLACK_SIGNING_SECRET': 'test_signing_secret'}):
            response = client.post('/slack/interactivity', 
                                 data=body,  # Send the raw body
                                 headers=headers)
            
    assert response.status_code == 200  # Slack expects 200 even for validation errors
    response_data = json.loads(response.data)
    assert response_data["ok"] is False
    assert response_data["error"] == "Missing required fields"

def test_invalid_signature(client):
    """Test that requests with invalid signatures are rejected."""
    data = {
        'command': '/leave',
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