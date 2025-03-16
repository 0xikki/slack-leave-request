from datetime import datetime
from typing import Dict, Any, Union, List

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
    return {
        "type": "modal",
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
                    "text": f"You are about to deny the leave request from <@{leave_request['user']['id']}>"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{leave_request['leave_type']}"
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
                "type": "input",
                "block_id": "denial_reason",
                "label": {
                    "type": "plain_text",
                    "text": "Reason for Denial",
                    "emoji": True
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "denial_reason_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Please provide a reason for denying this leave request..."
                    }
                }
            }
        ]
    } 