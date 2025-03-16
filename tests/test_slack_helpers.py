import pytest
from datetime import datetime
from src.slack.slack_helpers import (
    create_admin_notification_blocks,
    create_user_notification_blocks,
    create_denial_modal_view,
    format_date_for_display
)
import json

def test_create_admin_notification_blocks():
    """Test creation of admin notification blocks for a leave request."""
    # Test input
    user_id = "U123456"
    leave_type = "PTO"
    start_date = "2024-03-15"
    end_date = "2024-03-16"
    coverage_person = "U654321"
    tasks = "All tasks covered"
    reason = "Taking a vacation"
    
    blocks = create_admin_notification_blocks(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        coverage_person=coverage_person,
        tasks=tasks,
        reason=reason
    )
    
    # Verify the structure of the blocks
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Convert blocks to a string to easily check content
    blocks_str = str(blocks)
    
    # Check that all required information is present
    assert user_id in blocks_str  # User ID in mention format
    assert "March 15, 2024" in blocks_str  # Formatted start date
    assert "March 16, 2024" in blocks_str  # Formatted end date
    assert leave_type in blocks_str
    assert reason in blocks_str
    assert tasks in blocks_str
    assert coverage_person in blocks_str  # Covering user ID in mention format
    
    # Verify that approval and rejection buttons are present
    assert any(block.get("type") == "actions" for block in blocks)
    actions_block = next(block for block in blocks if block.get("type") == "actions")
    buttons = actions_block.get("elements", [])
    assert len(buttons) == 2
    assert any(btn.get("action_id") == "approve_leave" for btn in buttons)
    assert any(btn.get("action_id") == "reject_leave" for btn in buttons)

def test_create_user_notification_blocks():
    """Test creation of user notification blocks for request status."""
    # Test input
    user_id = "U123456"
    leave_type = "PTO"
    start_date = "2024-03-15"
    end_date = "2024-03-16"
    coverage_person = "U654321"
    tasks = "All tasks covered"
    reason = "Taking a vacation"
    
    blocks = create_user_notification_blocks(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        coverage_person=coverage_person,
        tasks=tasks,
        reason=reason
    )
    
    # Verify the structure
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Convert blocks to string for content checking
    blocks_str = str(blocks)
    
    # Check content
    assert "March 15, 2024" in blocks_str  # Formatted start date
    assert "March 16, 2024" in blocks_str  # Formatted end date
    assert leave_type in blocks_str
    assert tasks in blocks_str
    assert reason in blocks_str
    assert coverage_person in blocks_str

def test_create_denial_modal_view():
    """Test creation of the denial modal view."""
    # Test input
    leave_request = {
        'user': {'id': 'U123'},
        'channel_id': 'C456',
        'message_ts': '1234.5678',
        'leave_type': 'Sick/Emergency',
        'start_date': '2024-03-17',
        'end_date': '2024-03-18'
    }
    
    # Create modal view
    modal = create_denial_modal_view(leave_request)
    
    # Verify basic structure
    assert modal['type'] == 'modal'
    assert modal['callback_id'] == 'denial_modal'
    assert modal['title']['text'] == 'Deny Leave Request'
    
    # Verify private_metadata is present and contains correct data
    assert 'private_metadata' in modal, "private_metadata should be present in modal"
    metadata = json.loads(modal['private_metadata'])
    assert metadata['requester_id'] == 'U123'
    assert metadata['channel_id'] == 'C456'
    assert metadata['message_ts'] == '1234.5678'
    assert metadata['leave_type'] == 'Sick/Emergency'
    assert metadata['start_date'] == '2024-03-17'
    assert metadata['end_date'] == '2024-03-18'
    
    # Verify blocks structure
    blocks = modal['blocks']
    assert len(blocks) == 4  # Header, type, dates, and input
    
    # Verify input block
    input_block = next(b for b in blocks if b['type'] == 'input')
    assert input_block['block_id'] == 'denial_reason'
    assert input_block['element']['action_id'] == 'denial_reason_input'
    assert input_block['element']['multiline'] is True

def test_format_date_for_display():
    """Test date formatting for display."""
    # Test valid date string
    assert format_date_for_display("2024-03-15") == "March 15, 2024"
    
    # Test invalid date string
    assert format_date_for_display("invalid-date") == "invalid-date"  # Should return original string on error 