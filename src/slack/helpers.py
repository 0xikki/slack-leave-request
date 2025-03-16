from datetime import datetime
from typing import Dict, Any, Union, List
import json
import logging

logger = logging.getLogger(__name__)

def format_date_for_display(date: Union[str, datetime]) -> str:
    """Format a date for display in messages and modals."""
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
    return date.strftime("%B %d, %Y")

def create_admin_notification_blocks(leave_request: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create Block Kit blocks for admin notification of a new leave request."""
    user = leave_request["user"]
    covering_user = leave_request["covering_user"]
    
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🏖️ New Leave Request",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Requester:*\n<@{user['id']}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Type:*\n{leave_request['leave_type'].upper()}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Start Date:*\n{format_date_for_display(leave_request['start_date'])}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*End Date:*\n{format_date_for_display(leave_request['end_date'])}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{leave_request['reason']}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Tasks Coverage:*\n{leave_request['tasks_coverage']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Covered By:*\n<@{covering_user['id']}>"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": "approve",
                    "action_id": "approve_leave_hr"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Deny",
                        "emoji": True
                    },
                    "style": "danger",
                    "value": "deny",
                    "action_id": "reject_leave_hr"
                }
            ]
        }
    ]

def create_user_notification_blocks(request_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create Block Kit blocks for user notification of request status."""
    status = request_details["status"]
    status_emoji = "✅" if status == "approved" else "❌"
    status_color = "#2eb67d" if status == "approved" else "#e01e5a"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{status_emoji} Leave Request {status.title()}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Type:*\n{request_details['leave_type']}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Start Date:*\n{format_date_for_display(request_details['start_date'])}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*End Date:*\n{format_date_for_display(request_details['end_date'])}"
                }
            ]
        }
    ]
    
    if status == "denied" and "denial_reason" in request_details:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason for Denial:*\n{request_details['denial_reason']}"
                }
            }
        ])
    
    return blocks

def create_denial_modal_view(leave_request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a modal view for collecting denial reason."""
    # Create metadata for the modal
    metadata = {
        "requester_id": leave_request["user"]["id"],
        "channel_id": leave_request["channel_id"],
        "message_ts": leave_request["message_ts"],
        "leave_type": leave_request["leave_type"],
        "start_date": leave_request["start_date"],
        "end_date": leave_request.get("end_date", leave_request["start_date"])
    }
    
    # Format dates for display
    try:
        start_date_display = format_date_for_display(metadata["start_date"]) if metadata["start_date"] else "Not specified"
        end_date_display = format_date_for_display(metadata["end_date"]) if metadata["end_date"] else start_date_display
    except ValueError:
        # If date formatting fails, use the raw dates
        start_date_display = metadata["start_date"]
        end_date_display = metadata["end_date"]
    
    # Clean up leave type display (remove any escape characters)
    leave_type_display = metadata["leave_type"].replace("\\", "")
    
    modal = {
        "type": "modal",
        "callback_id": "denial_modal",
        "private_metadata": json.dumps(metadata),
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
        },
        "blocks": [
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
                        "text": f"*Type:*\n{leave_type_display}"
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
    }
    
    logger.info(f"Created modal view with callback_id: {modal.get('callback_id')} and private_metadata: {modal.get('private_metadata', 'NOT SET')}")
    return modal 