"""
Helper functions for creating Slack message blocks and views.
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

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

def create_denial_modal_view(requester_id: str) -> Dict[str, Any]:
    """Create a modal view for leave request rejection."""
    return {
        "type": "modal",
        "callback_id": "rejection_modal",
        "private_metadata": f'{{"requester_id": "{requester_id}"}}',
        "title": {
            "type": "plain_text",
            "text": "Reject Leave Request",
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
        },
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":x: Reject Leave Request",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Please provide a reason for rejecting this leave request:*"
                }
            },
            {
                "type": "input",
                "block_id": "rejection_reason_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "rejection_reason",
                    "multiline": True,
                    "min_length": 10,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter reason for rejection",
                        "emoji": True
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Rejection Reason",
                    "emoji": True
                }
            }
        ]
    }

def format_date_for_display(date_str: str) -> str:
    """Format a date string for display in Slack messages."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except ValueError as e:
        logger.error(f"Error formatting date {date_str}: {str(e)}")
        return date_str 