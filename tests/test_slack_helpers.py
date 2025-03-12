import pytest
from datetime import datetime
from src.slack.helpers import (
    create_admin_notification_blocks,
    create_user_notification_blocks,
    create_denial_modal_view,
    format_date_for_display
)

def test_create_admin_notification_blocks():
    """Test creation of admin notification blocks for a leave request."""
    leave_request = {
        "user": {"id": "U123456", "name": "john.doe"},
        "start_date": "2024-03-15",
        "end_date": "2024-03-16",
        "leave_type": "PTO",
        "reason": "Taking a vacation",
        "tasks_coverage": "All tasks covered",
        "covering_user": {"id": "U654321", "name": "jane.smith"}
    }
    
    blocks = create_admin_notification_blocks(leave_request)
    
    # Verify the structure of the blocks
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Convert blocks to a string to easily check content
    blocks_str = str(blocks)
    
    # Check that all required information is present
    assert "U123456" in blocks_str  # User ID in mention format
    assert "March 15, 2024" in blocks_str  # Formatted start date
    assert "March 16, 2024" in blocks_str  # Formatted end date
    assert "PTO" in blocks_str
    assert "Taking a vacation" in blocks_str
    assert "All tasks covered" in blocks_str
    assert "U654321" in blocks_str  # Covering user ID in mention format
    
    # Verify that approval and denial buttons are present
    assert any(block.get("type") == "actions" for block in blocks)
    actions_block = next(block for block in blocks if block.get("type") == "actions")
    buttons = actions_block.get("elements", [])
    assert len(buttons) == 2
    assert any(btn.get("value") == "approve" for btn in buttons)
    assert any(btn.get("value") == "deny" for btn in buttons)

def test_create_user_notification_blocks():
    """Test creation of user notification blocks for request status."""
    request_details = {
        "start_date": "2024-03-15",
        "end_date": "2024-03-16",
        "leave_type": "PTO",
        "status": "approved"
    }
    
    blocks = create_user_notification_blocks(request_details)
    
    # Verify the structure
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Convert blocks to string for content checking
    blocks_str = str(blocks)
    
    # Check content
    assert "approved" in blocks_str.lower()
    assert "March 15, 2024" in blocks_str  # Formatted start date
    assert "March 16, 2024" in blocks_str  # Formatted end date
    assert "PTO" in blocks_str

def test_create_denial_modal_view():
    """Test creation of the denial reason modal view."""
    leave_request = {
        "user": {"id": "U123456", "name": "john.doe"},
        "start_date": "2024-03-15",
        "end_date": "2024-03-16",
        "leave_type": "PTO"
    }
    
    view = create_denial_modal_view(leave_request)
    
    # Verify structure
    assert view["type"] == "modal"
    assert "title" in view
    assert "blocks" in view
    assert isinstance(view["blocks"], list)
    
    # Convert view to string for content checking
    view_str = str(view)
    
    # Check content
    assert "U123456" in view_str  # User ID in mention format
    assert "March 15, 2024" in view_str  # Formatted start date
    assert "March 16, 2024" in view_str  # Formatted end date
    assert "PTO" in view_str
    assert "reason" in view_str.lower()

def test_format_date_for_display():
    """Test date formatting for display."""
    # Test with string input
    assert format_date_for_display("2024-03-15") == "March 15, 2024"
    
    # Test with datetime input
    date = datetime(2024, 3, 15)
    assert format_date_for_display(date) == "March 15, 2024"
    
    # Test invalid date
    with pytest.raises(ValueError):
        format_date_for_display("invalid-date") 