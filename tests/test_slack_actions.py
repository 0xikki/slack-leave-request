import pytest
from unittest.mock import Mock, patch
from src.slack_actions import SlackActionsHandler

@pytest.fixture
def slack_actions_handler():
    """Create a SlackActionsHandler instance for testing."""
    return SlackActionsHandler()

@pytest.fixture
def sample_approval_payload():
    """Create a sample approval action payload."""
    return {
        "user": {"id": "ADMIN123", "name": "admin.user"},
        "actions": [{
            "action_id": "approve_leave",
            "value": "approve"
        }],
        "message": {
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {"text": "*Requester:*\n<@U123456>"},
                        {"text": "*Type:*\nPTO"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"text": "*Start Date:*\nMarch 15, 2024"},
                        {"text": "*End Date:*\nMarch 16, 2024"}
                    ]
                }
            ]
        }
    }

@pytest.fixture
def sample_denial_payload():
    """Create a sample denial action payload."""
    return {
        "user": {"id": "ADMIN123", "name": "admin.user"},
        "trigger_id": "test_trigger_123",
        "actions": [{
            "action_id": "deny_leave",
            "value": "deny"
        }],
        "message": {
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {"text": "*Requester:*\n<@U123456>"},
                        {"text": "*Type:*\nPTO"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"text": "*Start Date:*\nMarch 15, 2024"},
                        {"text": "*End Date:*\nMarch 16, 2024"}
                    ]
                }
            ]
        }
    }

def test_handle_approval_action(slack_actions_handler, sample_approval_payload):
    """Test handling of an approval action."""
    with patch('src.slack_actions.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat_postMessage.return_value = {"ok": True}
        
        # Set up the Slack token
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test_token'}):
            slack_actions_handler.client = mock_client
            response = slack_actions_handler.handle_action(sample_approval_payload)
        
        assert response["ok"] is True
        mock_client.chat_postMessage.assert_called_once()
        
        # Verify notification was sent to the user
        call_args = mock_client.chat_postMessage.call_args[1]
        blocks_str = str(call_args["blocks"])
        assert "approved" in blocks_str.lower()
        assert "March 15, 2024" in blocks_str
        assert "March 16, 2024" in blocks_str
        assert "PTO" in blocks_str

def test_handle_denial_action(slack_actions_handler, sample_denial_payload):
    """Test handling of a denial action."""
    with patch('src.slack_actions.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.views_open.return_value = {"ok": True}
        
        # Set up the Slack token
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test_token'}):
            slack_actions_handler.client = mock_client
            response = slack_actions_handler.handle_action(sample_denial_payload)
        
        assert response["ok"] is True
        mock_client.views_open.assert_called_once()
        
        # Verify denial modal was opened
        call_args = mock_client.views_open.call_args[1]
        view = call_args["view"]
        assert view["type"] == "modal"
        assert "Deny Leave Request" in str(view["title"])
        assert "denial_reason" in str(view["blocks"])

def test_handle_denial_submission(slack_actions_handler):
    """Test handling of a denial reason submission."""
    denial_submission = {
        "user": {"id": "ADMIN123"},
        "view": {
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Resource constraints"
                        }
                    }
                }
            },
            "private_metadata": '{"requester_id": "U123456", "leave_type": "PTO", "start_date": "2024-03-15", "end_date": "2024-03-16"}'
        }
    }
    
    with patch('src.slack_actions.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat_postMessage.return_value = {"ok": True}
        
        # Set up the Slack token
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test_token'}):
            slack_actions_handler.client = mock_client
            response = slack_actions_handler.handle_denial_submission(denial_submission)
        
        assert response["ok"] is True
        mock_client.chat_postMessage.assert_called_once()
        
        # Verify denial notification was sent to the user
        call_args = mock_client.chat_postMessage.call_args[1]
        blocks_str = str(call_args["blocks"])
        assert "denied" in blocks_str.lower()
        assert "Resource constraints" in blocks_str
        assert "March 15, 2024" in blocks_str
        assert "March 16, 2024" in blocks_str
        assert "PTO" in blocks_str

def test_handle_invalid_action(slack_actions_handler):
    """Test handling of an invalid action."""
    invalid_payload = {
        "user": {"id": "ADMIN123"},
        "actions": [{
            "action_id": "invalid_action",
            "value": "invalid"
        }]
    }
    
    response = slack_actions_handler.handle_action(invalid_payload)
    
    assert response["ok"] is False
    assert "error" in response
    assert "Invalid action" in response["error"]

def test_handle_missing_message_content(slack_actions_handler, sample_approval_payload):
    """Test handling of a payload with missing message content."""
    del sample_approval_payload["message"]
    
    response = slack_actions_handler.handle_action(sample_approval_payload)
    
    assert response["ok"] is False
    assert "error" in response
    assert "Missing message content" in response["error"] 