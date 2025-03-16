"""
Tests for the Slack actions handler.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.slack.slack_actions import SlackActionsHandler
import json
from slack_sdk.errors import SlackApiError

@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    client = MagicMock()
    # Set up default return values
    client.views_open.return_value = {"ok": True}
    client.chat_update.return_value = {"ok": True}
    client.chat_postMessage.return_value = {"ok": True}
    return client

@pytest.fixture
def slack_actions(mock_slack_client):
    """Create a SlackActionsHandler instance with a mock client."""
    return SlackActionsHandler(mock_slack_client)

def test_handle_dept_head_approval(slack_actions):
    """Test department head approval flow."""
    with patch('src.config.organization.is_department_head', return_value=True):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {"response_action": "clear"}

def test_handle_hr_approval(slack_actions):
    """Test HR approval flow."""
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {"response_action": "clear"}

def test_handle_dept_head_rejection(slack_actions):
    """Test department head rejection flow."""
    with patch('src.config.organization.is_department_head', return_value=True):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
            "trigger_id": "trigger123",
            "actions": [{"action_id": "reject_leave", "value": "reject"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {"response_action": "clear"}

def test_handle_rejection_submission(slack_actions):
    """Test handling of rejection reason submission."""
    payload = {
        "type": "view_submission",
        "user": {"id": "U06M5QCCLN9"},  # Development and Architecture head
        "view": {
            "callback_id": "denial_modal",
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
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Insufficient coverage"
                        }
                    }
                }
            }
        }
    }

    result = slack_actions.handle_view_submission(payload)
    assert result == {}

def test_invalid_action(slack_actions):
    """Test handling of invalid action."""
    payload = {
        "type": "block_actions",
        "user": {"id": "U06M5QCCLN9"},
        "actions": [{"action_id": "invalid_action", "value": "invalid"}],
        "container": {
            "type": "message",
            "message_ts": "1234567890.123456",
            "channel_id": "C1234567890"
        }
    }

    result = slack_actions.handle_action(payload)
    assert result == {
        "response_action": "errors",
        "errors": {"action": "Could not extract request details"}
    }

def test_unauthorized_approval(slack_actions):
    """Test unauthorized approval attempt."""
    with patch('src.config.organization.is_department_head', return_value=False), \
         patch('src.config.organization.load_admin_users', return_value=['U999XYZ']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06MKKWAWJX"},  # Regular team member
            "actions": [{"action_id": "approve_leave", "value": "approve"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {
            "response_action": "errors",
            "errors": {"action": "You are not authorized to perform this action"}
        }

def test_error_handling(mock_slack_client, monkeypatch):
    """Test error handling in actions."""
    # Setup
    handler = SlackActionsHandler(mock_slack_client)
    
    # Mock authorization to return True
    def mock_is_authorized(*args):
        return True
    monkeypatch.setattr(handler, "_is_authorized", mock_is_authorized)
    
    # Mock chat_update to raise an error
    mock_slack_client.chat_update.side_effect = SlackApiError(
        message="Error", response={"error": "channel_not_found"}
    )
    
    # Create a payload that will trigger the error
    payload = {
        "type": "block_actions",
        "user": {"id": "U123"},
        "actions": [{"action_id": "approve_leave"}],
        "container": {
            "channel_id": "C123",
            "message_ts": "123.456"
        },
        "message": {
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Requester:*\n<@U456>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Type:*\nVacation"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Start Date:*\n2024-03-20"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Coverage:*\nJohn Doe"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*End Date:*\n2024-03-22"
                        }
                    ]
                }
            ]
        }
    }
    
    # Test
    result = handler.handle_action(payload)
    
    # Assert
    assert result == {
        "response_action": "errors",
        "errors": {"action": "An error occurred while processing your request"}
    }
    
    # Verify the error was logged
    mock_slack_client.chat_update.assert_called_once()

def test_cannot_approve_own_request(slack_actions):
    """Test that a user cannot approve their own request."""
    with patch('src.config.organization.load_admin_users', return_value=[]):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06MKKWAWJX"},  # Regular team member
            "actions": [{"action_id": "approve_leave"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
            "message": {
                "blocks": [
                    {
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {
            "response_action": "errors",
            "errors": {"action": "You cannot approve or reject your own request"}
        }

def test_admin_can_approve_own_request(slack_actions):
    """Test that an admin can approve their own request."""
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "actions": [{"action_id": "approve_leave"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
            "message": {
                "blocks": [
                    {
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {"response_action": "clear"}

def test_handle_hr_rejection(slack_actions):
    """Test HR rejection flow."""
    with patch('src.config.organization.load_admin_users', return_value=['U06PNMDFVQW']):
        payload = {
            "type": "block_actions",
            "user": {"id": "U06PNMDFVQW"},  # HR member
            "trigger_id": "trigger123",
            "actions": [{"action_id": "reject_leave"}],
            "container": {
                "type": "message",
                "message_ts": "1234567890.123456",
                "channel_id": "C1234567890"
            },
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
                                "text": "*Start Date:*\n2024-03-20"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Coverage:*\nJohn Doe"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*End Date:*\n2024-03-22"
                            }
                        ]
                    }
                ]
            }
        }

        result = slack_actions.handle_action(payload)
        assert result == {"response_action": "clear"}

def test_missing_message(slack_actions):
    """Test handling of missing message in payload."""
    payload = {
        "type": "block_actions",
        "user": {"id": "U06PNMDFVQW"},
        "actions": [{"action_id": "approve_leave"}],
        "container": {
            "type": "message",
            "message_ts": "1234567890.123456",
            "channel_id": "C1234567890"
        }
    }

    result = slack_actions.handle_action(payload)
    assert result == {
        "response_action": "errors",
        "errors": {"action": "Could not extract request details"}
    }

def test_handle_view_submission_denial_modal_with_callback_id(slack_actions):
    """Test handling view submission for denial modal with callback_id."""
    payload = {
        "view": {
            "callback_id": "denial_modal",
            "private_metadata": json.dumps({
                "requester_id": "U123",
                "channel_id": "C123",
                "message_ts": "123.456"
            }),
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Not approved"
                        }
                    }
                }
            }
        }
    }
    
    result = slack_actions.handle_view_submission(payload)
    assert result == {}, "Should return empty dict to close modal"

def test_handle_view_submission_denial_modal_without_callback_id(slack_actions):
    """Test handling view submission for denial modal without callback_id (fallback)."""
    payload = {
        "view": {
            "private_metadata": json.dumps({
                "requester_id": "U123",
                "channel_id": "C123",
                "message_ts": "123.456"
            }),
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Not approved"
                        }
                    }
                }
            }
        }
    }
    
    result = slack_actions.handle_view_submission(payload)
    assert result == {}, "Should return empty dict to close modal"

def test_handle_view_submission_denial_modal_missing_reason(slack_actions):
    """Test handling view submission for denial modal with missing reason."""
    payload = {
        "view": {
            "callback_id": "denial_modal",
            "private_metadata": json.dumps({
                "requester_id": "U123",
                "channel_id": "C123",
                "message_ts": "123.456"
            }),
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": ""
                        }
                    }
                }
            }
        }
    }
    
    result = slack_actions.handle_view_submission(payload)
    assert result == {
        "response_action": "errors",
        "errors": {
            "denial_reason": "Please provide a reason for rejection"
        }
    }

def test_handle_view_submission_denial_modal_invalid_metadata(slack_actions):
    """Test handling view submission for denial modal with invalid metadata."""
    payload = {
        "view": {
            "callback_id": "denial_modal",
            "private_metadata": "invalid json",
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Not approved"
                        }
                    }
                }
            }
        }
    }
    
    result = slack_actions.handle_view_submission(payload)
    assert result == {
        "response_action": "errors",
        "errors": {
            "submission": "Invalid request metadata. Please try again."
        }
    }

def test_handle_view_submission_denial_modal_missing_metadata_fields(slack_actions):
    """Test handling view submission for denial modal with missing metadata fields."""
    payload = {
        "view": {
            "callback_id": "denial_modal",
            "private_metadata": json.dumps({
                "requester_id": "U123"  # Missing channel_id and message_ts
            }),
            "state": {
                "values": {
                    "denial_reason": {
                        "denial_reason_input": {
                            "value": "Not approved"
                        }
                    }
                }
            }
        }
    }
    
    result = slack_actions.handle_view_submission(payload)
    assert result == {
        "response_action": "errors",
        "errors": {
            "submission": "Invalid request data. Please try again."
        }
    }