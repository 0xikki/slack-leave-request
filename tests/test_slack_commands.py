"""
Tests for the Slack commands handler.
"""
import pytest
from unittest.mock import patch, MagicMock
from slack_sdk.errors import SlackApiError
from src.slack.slack_commands import SlackCommandsHandler

@pytest.fixture
def mock_slack_client():
    """Create a mock Slack client."""
    return MagicMock()

@pytest.fixture
def command_handler(mock_slack_client):
    """Create a SlackCommandsHandler instance for testing."""
    return SlackCommandsHandler(mock_slack_client)

@pytest.fixture
def sample_command_payload():
    """Create a sample command payload."""
    return {
        'command': '/timeoff',
        'trigger_id': 'T123',
        'user_id': 'U123'
    }

def test_leave_command_opens_modal():
    """Test that the /leave command opens a modal with correct fields."""
    with patch('src.slack.slack_commands.WebClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        handler = SlackCommandsHandler(mock_client)
        result = handler.handle_command({
            "trigger_id": "123.456.abc",
            "user_id": "U123ABC",
            "command": "/leave"
        })

        mock_client.views_open.assert_called_once()
        view_args = mock_client.views_open.call_args[1]['view']

        # Verify modal structure
        assert view_args['type'] == 'modal'
        assert view_args['title']['text'] == 'Submit Leave Request'

        # Verify required blocks are present
        block_ids = [block.get('block_id', '') for block in view_args['blocks']]
        required_blocks = [
            'leave_type_block',
            'date_block',
            'coverage_block',
            'tasks_block',
            'reason_block'
        ]
        for block in required_blocks:
            assert block in block_ids

def test_leave_command_validates_user():
    """Test that the command validates the user before proceeding."""
    with patch('src.slack.slack_commands.WebClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        handler = SlackCommandsHandler(mock_client)
        result = handler.handle_command({
            "trigger_id": "123.456.abc",
            "command": "/leave"
        })

        assert result["ok"] is False
        assert "Missing user_id" in result["error"]

def test_leave_command_validates_trigger():
    """Test that the command validates the trigger_id before proceeding."""
    with patch('src.slack.slack_commands.WebClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        handler = SlackCommandsHandler(mock_client)
        result = handler.handle_command({
            "user_id": "U123ABC",
            "command": "/leave"
        })

        assert result["ok"] is False
        assert "No trigger_id provided" in result["error"]

def test_load_modal_template_success(command_handler):
    """Test that the modal template is loaded correctly."""
    modal = command_handler._load_modal_template()

    assert modal["type"] == "modal"
    assert modal["callback_id"] == "leave_request_modal"
    assert "blocks" in modal

    # Verify required fields are present
    block_ids = [block.get("block_id") for block in modal["blocks"]]
    required_fields = [
        'leave_type_block',
        'date_block',
        'coverage_block',
        'tasks_block',
        'reason_block'
    ]

    for field in required_fields:
        assert field in block_ids, f"Missing required field: {field}"

def test_load_modal_template_fallback(command_handler):
    """Test that a fallback template is returned when the file is not found."""
    with patch('pathlib.Path.open', side_effect=FileNotFoundError):
        modal = command_handler._load_modal_template()
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "leave_request_modal"
        assert len(modal["blocks"]) > 0

def test_leave_request_notification_format():
    """Test the format of leave request notifications for different leave types."""
    with patch('src.slack.slack_commands.WebClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        handler = SlackCommandsHandler(mock_client)
        
        # Test each leave type
        leave_types = [
            ("PTO", "pto"),
            ("Sick/Emergency", "sick_emergency"),
            ("Holiday", "holiday"),
            ("Offset", "offset")
        ]
        
        for display_text, value in leave_types:
            handler.handle_modal_submission({
                "type": "view_submission",
                "user": {"id": "U123ABC", "name": "testuser"},
                "view": {
                    "state": {
                        "values": {
                            "leave_type_block": {"leave_type": {"selected_option": {"text": {"type": "plain_text", "text": display_text}, "value": value}}},
                            "date_block": {
                                "start_date": {"selected_date": "2024-03-20"}
                            },
                            "coverage_block": {"coverage_person": {"selected_user": "U456DEF"}},
                            "tasks_block": {"tasks": {"value": "Test tasks"}},
                            "reason_block": {"reason": {"value": "Test reason"}}
                        }
                    }
                }
            })

            # Verify notification format
            message_args = mock_client.chat_postMessage.call_args[1]
            assert "blocks" in message_args
            blocks = message_args["blocks"]

            # Verify block structure
            assert len(blocks) > 0
            assert blocks[0]["type"] == "section"
            assert "fields" in blocks[0]
            
            # Verify leave type is correctly displayed
            type_field = next(field for field in blocks[0]["fields"] if "*Type:*" in field["text"])
            assert display_text in type_field["text"], f"Expected '{display_text}' in notification, but got '{type_field['text']}'"
            assert value not in type_field["text"], f"Found value '{value}' in notification when it should show display text"

def test_handle_timeoff_command(command_handler, sample_command_payload):
    """Test handling of the /timeoff command."""
    # Mock the Slack client methods
    command_handler.client.views_open.return_value = {"ok": True}

    response = command_handler.handle_command(sample_command_payload)

    assert response["ok"] is True
    assert "Opening leave request form" in response["text"]

def test_handle_invalid_command(command_handler):
    """Test handling of an invalid command."""
    payload = {
        'command': '/invalid',
        'user_id': 'U123',
        'trigger_id': 'T123'
    }

    response = command_handler.handle_command(payload)

    assert response["ok"] is False
    assert "Invalid command" in response["error"]

def test_handle_slack_api_error(command_handler, sample_command_payload):
    """Test handling of Slack API errors."""
    # Mock the Slack client to raise an API error
    command_handler.client.views_open.side_effect = SlackApiError(
        "error",
        {"error": "invalid_trigger_id"}
    )

    response = command_handler.handle_command(sample_command_payload)

    assert response["ok"] is False
    assert "Failed to open leave request form" in response["error"]

def test_modal_template_loading(command_handler):
    """Test that the modal template is loaded correctly."""
    modal = command_handler._load_modal_template()

    assert modal["type"] == "modal"
    assert modal["callback_id"] == "leave_request_modal"
    assert "blocks" in modal

    # Verify required fields are present
    block_ids = [block.get("block_id") for block in modal["blocks"]]
    required_fields = [
        'leave_type_block',
        'date_block',
        'coverage_block',
        'tasks_block',
        'reason_block'
    ]

    for field in required_fields:
        assert field in block_ids, f"Missing required field: {field}" 