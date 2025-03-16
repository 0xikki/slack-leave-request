"""
Tests for the Slack actions handler.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.slack.slack_actions import SlackActionsHandler
import json

@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    return MagicMock()

def test_handle_dept_head_approval(mock_slack_client):
    """Test department head approval flow."""
    handler = SlackActionsHandler(mock_slack_client)

    # Mock department head check using actual department head ID
    with patch('src.config.organization.is_department_head', return_value=True):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "message": {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Requester:*\n<@U06MKKWAWJX>"  # Team member
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Type:*\nAnnual Leave"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                            }
                        ]
                    }
                ],
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"}
            }
        }

        result = handler.handle_action(payload)

        assert result["response_action"] == "clear"
        mock_slack_client.chat_update.assert_called_once()
        mock_slack_client.chat_postMessage.assert_called_once()

def test_handle_hr_approval(mock_slack_client):
    """Test HR approval flow."""
    handler = SlackActionsHandler(mock_slack_client)

    # Mock HR member check using actual HR member ID
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "message": {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Requester:*\n<@U06MKKWAWJX>"  # Team member
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Type:*\nAnnual Leave"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                            }
                        ]
                    }
                ],
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"}
            }
        }

        result = handler.handle_action(payload)

        assert result["response_action"] == "clear"
        mock_slack_client.chat_update.assert_called_once()
        mock_slack_client.chat_postMessage.assert_called_once()

def test_handle_dept_head_rejection(mock_slack_client):
    """Test department head rejection flow."""
    handler = SlackActionsHandler(mock_slack_client)

    with patch('src.config.organization.is_department_head', return_value=True):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
            "trigger_id": "trigger123",
            "actions": [{"action_id": "reject_leave", "value": "reject"}],
            "message": {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Requester:*\n<@U06MKKWAWJX>"  # Team member
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Type:*\nAnnual Leave"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                            }
                        ]
                    }
                ],
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"}
            }
        }

        result = handler.handle_action(payload)

        assert result["response_action"] == "clear"
        mock_slack_client.views_open.assert_called_once()

def test_handle_rejection_submission(mock_slack_client):
    """Test handling of rejection reason submission."""
    handler = SlackActionsHandler(mock_slack_client)

    payload = {
        "type": "view_submission",
        "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
        "view": {
            "callback_id": "rejection_modal",
            "private_metadata": json.dumps({
                "requester_id": "U06MKKWAWJX",
                "channel_id": "C1234567890",
                "message_ts": "1234567890.123456",
                "leave_type": "Annual Leave",
                "start_date": "2024-03-20",
                "end_date": "2024-03-22"
            }),
            "state": {
                "values": {
                    "rejection_reason_block": {
                        "rejection_reason": {
                            "value": "Insufficient coverage"
                        }
                    }
                }
            }
        }
    }

    result = handler.handle_view_submission(payload)

    assert result["response_action"] == "clear"
    mock_slack_client.chat_update.assert_called_once()
    mock_slack_client.chat_postMessage.assert_called_once()

def test_invalid_action(mock_slack_client):
    """Test handling of invalid action."""
    handler = SlackActionsHandler(mock_slack_client)

    payload = {
        "type": "block_actions",
        "user": {"id": "U06M5QCCLN9"},
        "actions": [{"action_id": "invalid_action", "value": "invalid"}]
    }

    result = handler.handle_action(payload)

    assert result["response_action"] == "errors"
    assert result["errors"]["action"] == "Invalid action"

def test_unauthorized_approval(mock_slack_client):
    """Test unauthorized approval attempt."""
    handler = SlackActionsHandler(mock_slack_client)

    # Mock checks to return False
    with patch('src.config.organization.is_department_head', return_value=False), \
         patch('src.config.organization.load_admin_users', return_value=['U999XYZ']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06MKKWAWJX"},  # Regular team member
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "message": {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Requester:*\n<@U06PNMDFVQW>"  # HR member
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Type:*\nAnnual Leave"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = handler.handle_action(payload)

        assert result["response_action"] == "errors"
        assert result["errors"]["action"] == "You are not authorized to perform this action"

def test_error_handling(mock_slack_client):
    """Test error handling in actions."""
    handler = SlackActionsHandler(mock_slack_client)

    # Mock authorization to pass but API call to fail
    with patch('src.config.organization.is_department_head', return_value=True):
        # Simulate API error
        mock_slack_client.chat_update.side_effect = Exception("API Error")

        payload = {
            "type": "block_actions",
            "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "message": {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Requester:*\n<@U06MKKWAWJX>"  # Team member
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Type:*\nAnnual Leave"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                            }
                        ]
                    }
                ],
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"}
            }
        }

        result = handler.handle_action(payload)

        assert result["response_action"] == "errors"
        assert result["errors"]["action"] == "API Error: API Error"

def test_cannot_approve_own_request(mock_slack_client):
    """Test that a user cannot approve their own request."""
    handler = SlackActionsHandler(mock_slack_client)
    
    # Mock user is not an admin
    with patch('src.config.organization.load_admin_users', return_value=[]):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06MKKWAWJX"},  # Regular team member
            "actions": [{"action_id": "approve_leave"}],
            "message": {
                "type": "message",
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"},
                "blocks": [{
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Requester:*\n<@U06MKKWAWJX>"  # Same as approver
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Type:*\nAnnual Leave"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                        }
                    ]
                }]
            }
        }

        result = handler.handle_action(payload)

        assert result == {
            "response_action": "errors",
            "errors": {"action": "You cannot approve or reject your own request"}
        }

def test_admin_can_approve_own_request(mock_slack_client):
    """Test that an admin can approve their own request."""
    handler = SlackActionsHandler(mock_slack_client)
    
    # Mock user is an admin
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "actions": [{"action_id": "approve_leave"}],
            "message": {
                "type": "message",
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"},
                "blocks": [{
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Requester:*\n<@U06PNMDFVQW>"  # Same as approver
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Type:*\nAnnual Leave"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                        }
                    ]
                }]
            }
        }

        result = handler.handle_action(payload)

        assert result == {"response_action": "clear"}
        mock_slack_client.chat_update.assert_called_once()
        mock_slack_client.chat_postMessage.assert_called_once()

def test_handle_hr_rejection(mock_slack_client):
    """Test HR rejection flow."""
    handler = SlackActionsHandler(mock_slack_client)
    
    # Mock user is an admin
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "trigger_id": "trigger123",
            "actions": [{"action_id": "reject_leave"}],
            "message": {
                "type": "message",
                "ts": "1234567890.123456",
                "channel": {"id": "C1234567890"},
                "blocks": [{
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Requester:*\n<@U06MKKWAWJX>"  # Team member
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Type:*\nAnnual Leave"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Duration:*\n2024-03-20 to 2024-03-22"
                        }
                    ]
                }]
            }
        }

        result = handler.handle_action(payload)

        assert result == {"response_action": "clear"}
        mock_slack_client.views_open.assert_called_once()

def test_missing_message(mock_slack_client):
    """Test handling of missing message in payload."""
    handler = SlackActionsHandler(mock_slack_client)
    payload = {
        "type": "block_actions",
        "user": {"id": "U06PNMDFVQW"},
        "actions": [{"action_id": "approve_leave"}]
    }

    result = handler.handle_action(payload)

    assert result == {
        "response_action": "errors",
        "errors": {"action": "Could not extract request details"}
    }