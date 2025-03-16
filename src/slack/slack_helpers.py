"""
Helper functions for creating Slack message blocks and views.
"""
from typing import Dict, Any, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

def create_admin_notification_blocks(user_id: str, leave_type: str, start_date: str,
                                  end_date: str, coverage_person: str, tasks: str, reason: str, **kwargs) -> List[Dict[str, Any]]:
    """Create notification blocks for admin/department head."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":memo: New Leave Request",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Requester:*\n<@{user_id}>"},
                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                {"type": "mrkdwn", "text": f"*Start Date:*\n{format_date_for_display(start_date)}"},
                {"type": "mrkdwn", "text": f"*End Date:*\n{format_date_for_display(end_date)}"},
                {"type": "mrkdwn", "text": f"*Coverage:*\n<@{coverage_person}>"},
                {"type": "mrkdwn", "text": f"*Tasks:*\n{tasks}"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{reason}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve",
                        "emoji": True
                    },
                    "style": "primary",
                    "action_id": "approve_leave"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Reject",
                        "emoji": True
                    },
                    "style": "danger",
                    "action_id": "reject_leave"
                }
            ]
        }
    ]

def create_user_notification_blocks(user_id: str, leave_type: str, start_date: str,
                                 end_date: str, coverage_person: str, tasks: str, reason: str, **kwargs) -> List[Dict[str, Any]]:
    """Create notification blocks for the requesting user."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":memo: Leave Request Submitted",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                {"type": "mrkdwn", "text": f"*Start Date:*\n{format_date_for_display(start_date)}"},
                {"type": "mrkdwn", "text": f"*End Date:*\n{format_date_for_display(end_date)}"},
                {"type": "mrkdwn", "text": f"*Coverage:*\n<@{coverage_person}>"},
                {"type": "mrkdwn", "text": f"*Tasks:*\n{tasks}"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{reason}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":information_source: Your request has been submitted and is pending approval."
                }
            ]
        }
    ]

def create_denial_modal_view(leave_request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a modal view for collecting denial reason."""
    # Create metadata with all necessary information
    metadata = {
        "requester_id": leave_request['user']['id'],
        "channel_id": leave_request.get('channel_id'),
        "message_ts": leave_request.get('message_ts'),
        "leave_type": leave_request.get('leave_type'),
        "start_date": leave_request.get('start_date'),
        "end_date": leave_request.get('end_date', leave_request.get('start_date'))  # Default to start_date if no end_date
    }
    
    # Format dates for display
    start_date_display = format_date_for_display(metadata['start_date']) if metadata['start_date'] else 'Not specified'
    end_date_display = format_date_for_display(metadata['end_date']) if metadata['end_date'] else start_date_display
    
    # Create the basic modal structure first
    modal = {
        "type": "modal",
        "callback_id": "denial_modal",
        "title": {
            "type": "plain_text",
            "text": "Deny Leave Request",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        }
    }
    
    # Add metadata
    modal["private_metadata"] = json.dumps(metadata)
    
    # Add blocks
    modal["blocks"] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"You are about to deny the leave request from <@{metadata['requester_id']}>"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Type:*\n{metadata['leave_type']}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Start Date:*\n{start_date_display}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*End Date:*\n{end_date_display}"
                }
            ]
        },
        {
            "type": "input",
            "block_id": "denial_reason",
            "element": {
                "type": "plain_text_input",
                "action_id": "denial_reason_input",
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Please provide a reason for denying this leave request...",
                    "emoji": True
                }
            },
            "label": {
                "type": "plain_text",
                "text": "Reason for Denial",
                "emoji": True
            }
        }
    ]
    
    logger.info(f"Created modal view with callback_id: {modal.get('callback_id')} and private_metadata: {modal.get('private_metadata', 'NOT SET')}")
    return modal

def format_date_for_display(date_str: str) -> str:
    """Format a date string for display in Slack messages."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except ValueError as e:
        logger.error(f"Error formatting date {date_str}: {str(e)}")
        return date_str 