import pytest
from src.slack_commands import SlackCommandHandler
from unittest.mock import Mock, patch
import json
from pathlib import Path
import os

@pytest.fixture
def slack_command_handler():
    """Create a SlackCommandHandler instance for testing."""
    return SlackCommandHandler()

@pytest.fixture
def sample_modal_submission():
    """Create a sample modal submission payload."""
    return {
        "user": {"id": "U123456", "name": "test.user"},
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
                            "value": "Project X handover"
                        }
                    },
                    "covering_person": {
                        "covering_user_select": {
                            "selected_user": "U789012"
                        }
                    }
                }
            }
        }
    }

def test_leave_command_opens_modal():
    """Test that the /leave command triggers opening a modal."""
    with patch('src.slack_commands.WebClient') as mock_client_class:
        # Set up the mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.views_open.return_value = {"ok": True}
        
        handler = SlackCommandHandler()
        response = handler.handle_leave_command(
            user_id="U123456",
            trigger_id="trigger123"
        )
        
        assert response["ok"] is True
        mock_client.views_open.assert_called_once()
        # Verify the view argument was passed
        call_args = mock_client.views_open.call_args[1]
        assert "trigger_id" in call_args
        assert "view" in call_args
        assert call_args["trigger_id"] == "trigger123"

def test_leave_command_validates_user():
    """Test that the command validates the user before proceeding."""
    with patch('src.slack_commands.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        handler = SlackCommandHandler()
        
        response = handler.handle_leave_command(
            user_id=None,
            trigger_id="trigger123"
        )
        
        assert response["ok"] is False
        assert "error" in response
        assert "Invalid user" in response["error"]
        mock_client.views_open.assert_not_called()

def test_leave_command_validates_trigger():
    """Test that the command validates the trigger_id before proceeding."""
    with patch('src.slack_commands.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        handler = SlackCommandHandler()
        
        response = handler.handle_leave_command(
            user_id="U123456",
            trigger_id=None
        )
        
        assert response["ok"] is False
        assert "error" in response
        assert "Invalid trigger" in response["error"]
        mock_client.views_open.assert_not_called()

def test_load_modal_template_success():
    """Test that the modal template is loaded correctly."""
    handler = SlackCommandHandler()
    template = handler._load_modal_template()
    
    assert template["type"] == "modal"
    assert template["callback_id"] == "leave_request_modal"
    assert len(template["blocks"]) > 0
    
    # Verify required fields are present
    blocks = {block.get("block_id"): block for block in template["blocks"] if "block_id" in block}
    assert "leave_dates" in blocks
    assert "leave_type" in blocks
    assert "leave_reason" in blocks
    assert "tasks_coverage" in blocks
    assert "covering_person" in blocks

def test_load_modal_template_fallback():
    """Test that a fallback template is returned when the file is not found."""
    with patch('pathlib.Path.open', side_effect=FileNotFoundError):
        handler = SlackCommandHandler()
        template = handler._load_modal_template()
        
        assert template["type"] == "modal"
        assert "blocks" in template
        assert len(template["blocks"]) > 0

def test_handle_modal_submission_success(slack_command_handler, sample_modal_submission):
    """Test successful handling of a modal submission."""
    with patch('src.slack_commands.WebClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.chat_postMessage.return_value = {"ok": True}
        
        # Set up the admin channel
        slack_command_handler.admin_channel = "admin-channel"
        
        # Set up the Slack token
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test_token'}):
            # Create a new client with the mocked token
            slack_command_handler.client = mock_client
            response = slack_command_handler.handle_modal_submission(sample_modal_submission)
        
        assert response["ok"] is True
        mock_client.chat_postMessage.assert_called_once()
        
        # Verify the message was sent to the admin channel with the correct blocks
        call_args = mock_client.chat_postMessage.call_args[1]
        assert call_args["channel"] == "admin-channel"
        assert "blocks" in call_args
        
        # Convert blocks to string for content checking
        blocks_str = str(call_args["blocks"])
        assert "U123456" in blocks_str  # Requester ID
        assert "March 15, 2024" in blocks_str  # Start date
        assert "March 16, 2024" in blocks_str  # End date
        assert "PTO" in blocks_str
        assert "Taking a vacation" in blocks_str
        assert "Project X handover" in blocks_str
        assert "U789012" in blocks_str  # Covering user ID
        
        # Verify approval/denial buttons
        blocks = call_args["blocks"]
        actions_block = next(block for block in blocks if block["type"] == "actions")
        buttons = actions_block["elements"]
        assert len(buttons) == 2
        assert any(btn["value"] == "approve" for btn in buttons)
        assert any(btn["value"] == "deny" for btn in buttons)

def test_handle_modal_submission_missing_required(slack_command_handler):
    """Test handling of a modal submission with missing required fields."""
    incomplete_submission = {
        "user": {"id": "U123456"},
        "view": {
            "state": {
                "values": {
                    "leave_dates": {},  # Missing start date
                    "leave_type": {
                        "leave_type_select": {
                            "selected_option": {
                                "value": "pto"
                            }
                        }
                    }
                }
            }
        }
    }

    response = slack_command_handler.handle_modal_submission(incomplete_submission)

    assert response["ok"] is False
    assert "error" in response
    assert "Start date and end date are required" in response["error"]

def test_handle_modal_submission_invalid_dates(slack_command_handler, sample_modal_submission):
    """Test handling of a modal submission with invalid dates."""
    # Modify end date to be before start date
    sample_modal_submission["view"]["state"]["values"]["leave_dates"]["start_date"]["selected_date"] = "2024-03-15"
    sample_modal_submission["view"]["state"]["values"]["leave_dates"]["end_date"]["selected_date"] = "2024-03-14"

    response = slack_command_handler.handle_modal_submission(sample_modal_submission)

    assert response["ok"] is False
    assert "error" in response
    assert "End date must be after start date" in response["error"] 