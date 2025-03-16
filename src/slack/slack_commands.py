from typing import Dict, Any, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
import json
import logging
from datetime import datetime
from src.config.organization import is_department_head, get_department_head, HR_CHANNEL_ID, get_department_name
from src.slack.helpers import format_date_for_display, create_admin_notification_blocks, create_user_notification_blocks

logger = logging.getLogger(__name__)

class SlackCommandsHandler:
    """Handler for Slack slash commands."""

    def __init__(self, client: WebClient):
        """Initialize with Slack client."""
        self.client = client

    def handle_command(self, payload):
        """Handle slash commands."""
        try:
            command = payload.get("command", "")

            if command == "/timeoff" or command == "/leave":
                return self._handle_timeoff_command(payload)
            else:
                return {
                    "ok": False,
                    "error": "Invalid command",
                    "response_type": "ephemeral",
                    "text": "Invalid command",
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: Invalid command. Use `/leave` or `/timeoff` to submit a leave request."
                        }
                    }]
                }

        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return {
                "ok": False,
                "error": str(e),
                "response_type": "ephemeral",
                "text": "An error occurred",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":x: An error occurred while processing your request. Please try again later."
                    }
                }]
            }

    def _handle_timeoff_command(self, payload):
        """Handle /timeoff command."""
        try:
            # Validate required fields
            if "user_id" not in payload:
                return {
                    "ok": False,
                    "error": "Missing user_id",
                    "response_type": "ephemeral",
                    "text": "Missing user_id",
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: Could not identify the user. Please try again."
                        }
                    }]
                }
            if "trigger_id" not in payload:
                return {
                    "ok": False,
                    "error": "No trigger_id provided",
                    "response_type": "ephemeral",
                    "text": "No trigger_id provided",
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: Invalid request. Please try again."
                        }
                    }]
                }

            # Open modal
            self.client.views_open(
                trigger_id=payload["trigger_id"],
                view=self._load_modal_template()
            )

            return {
                "ok": True,
                "response_type": "ephemeral",
                "text": "Opening leave request form...",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":memo: Opening the leave request form..."
                    }
                }]
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {
                "ok": False,
                "error": f"Failed to open leave request form: {e.response['error']}",
                "response_type": "ephemeral",
                "text": f"Failed to open leave request form: {e.response['error']}",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":x: Failed to open leave request form: {e.response['error']}"
                    }
                }]
            }
        except Exception as e:
            logger.error(f"Error handling timeoff command: {e}")
            return {
                "ok": False,
                "error": str(e),
                "response_type": "ephemeral",
                "text": "An error occurred",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":x: An error occurred while processing your request. Please try again later."
                    }
                }]
            }

    def _load_modal_template(self):
        """Load the modal template from file."""
        try:
            template_path = Path(__file__).parent / 'templates' / 'leave_request_modal.json'
            with open(template_path, 'r') as f:
                modal = json.load(f)
                return modal
        except FileNotFoundError:
            # Fallback to default template with updated Block Kit features
            return {
                "type": "modal",
                "callback_id": "leave_request_modal",
                "title": {"type": "plain_text", "text": "Submit Leave Request", "emoji": True},
                "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
                "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":calendar: Leave Request Details",
                            "emoji": True
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "leave_type_block",
                        "element": {
                            "type": "static_select",
                            "action_id": "leave_type",
                            "placeholder": {"type": "plain_text", "text": "Select leave type", "emoji": True},
                            "options": [
                                {"text": {"type": "plain_text", "text": "PTO", "emoji": True}, "value": "pto"},
                                {"text": {"type": "plain_text", "text": "Sick Leave", "emoji": True}, "value": "sick"}
                            ]
                        },
                        "label": {"type": "plain_text", "text": "Leave Type", "emoji": True}
                    },
                    {
                        "type": "input",
                        "block_id": "date_block",
                        "element": {
                            "type": "datepicker",
                            "action_id": "start_date",
                            "placeholder": {"type": "plain_text", "text": "Select start date", "emoji": True},
                            "initial_date": datetime.now().strftime("%Y-%m-%d")
                        },
                        "label": {"type": "plain_text", "text": "Start Date", "emoji": True}
                    },
                    {
                        "type": "input",
                        "block_id": "end_date_block",
                        "element": {
                            "type": "datepicker",
                            "action_id": "end_date",
                            "placeholder": {"type": "plain_text", "text": "Select end date", "emoji": True},
                            "initial_date": datetime.now().strftime("%Y-%m-%d")
                        },
                        "label": {"type": "plain_text", "text": "End Date", "emoji": True}
                    },
                    {
                        "type": "input",
                        "block_id": "coverage_block",
                        "element": {
                            "type": "users_select",
                            "action_id": "coverage_person",
                            "placeholder": {"type": "plain_text", "text": "Select a person", "emoji": True}
                        },
                        "label": {"type": "plain_text", "text": "Who will cover for you?", "emoji": True}
                    },
                    {
                        "type": "input",
                        "block_id": "tasks_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "tasks",
                            "multiline": True,
                            "placeholder": {"type": "plain_text", "text": "List your tasks", "emoji": True}
                        },
                        "label": {"type": "plain_text", "text": "Tasks to be covered", "emoji": True}
                    },
                    {
                        "type": "input",
                        "block_id": "reason_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "reason",
                            "placeholder": {"type": "plain_text", "text": "Enter your reason", "emoji": True}
                        },
                        "label": {"type": "plain_text", "text": "Reason for leave", "emoji": True}
                    }
                ]
            }

    def handle_modal_submission(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle modal submission for leave request."""
        try:
            # Extract user details
            user = payload.get("user", {})
            user_id = user.get("id")
            user_name = user.get("name")

            if not user_id or not user_name:
                return {
                    "response_action": "errors",
                    "errors": {
                        "user": "Could not extract user details"
                    }
                }

            # Extract form values
            values = payload.get("view", {}).get("state", {}).get("values", {})
            
            # Extract leave type
            leave_type_block = values.get("leave_type_block", {})
            leave_type = leave_type_block.get("leave_type", {}).get("selected_option", {}).get("value")
            if not leave_type:
                return {
                    "response_action": "errors",
                    "errors": {
                        "leave_type_block": "Please select a leave type"
                    }
                }

            # Extract dates
            date_block = values.get("date_block", {})
            start_date = date_block.get("start_date", {}).get("selected_date")
            if not start_date:
                return {
                    "response_action": "errors",
                    "errors": {
                        "date_block": "Please select a start date"
                    }
                }

            # Extract coverage person
            coverage_block = values.get("coverage_block", {})
            coverage_person = coverage_block.get("coverage_person", {}).get("selected_user")
            if not coverage_person:
                return {
                    "response_action": "errors",
                    "errors": {
                        "coverage_block": "Please select who will cover for you"
                    }
                }

            # Extract tasks and reason
            tasks = values.get("tasks_block", {}).get("tasks", {}).get("value")
            reason = values.get("reason_block", {}).get("reason", {}).get("value")
            if not tasks or not reason:
                errors = {}
                if not tasks:
                    errors["tasks_block"] = "Please list tasks to be covered"
                if not reason:
                    errors["reason_block"] = "Please provide a reason"
                return {
                    "response_action": "errors",
                    "errors": errors
                }

            # Create notification blocks
            notification_blocks = [
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Requester:*\n<@{user_id}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{leave_type}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{start_date}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Coverage:*\n<@{coverage_person}>"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Tasks:*\n{tasks}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{reason}"
                        }
                    ]
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

            # Send notification to user
            self.client.chat_postMessage(
                channel=user_id,
                text="Your leave request has been submitted",
                blocks=notification_blocks
            )

            # Send notification to HR channel
            hr_channel = get_hr_channel_id()
            if hr_channel:
                self.client.chat_postMessage(
                    channel=hr_channel,
                    text=f"New leave request from <@{user_id}>",
                    blocks=notification_blocks
                )

            return {"response_action": "clear"}

        except Exception as e:
            logger.error(f"Error handling modal submission: {str(e)}")
            return {
                "response_action": "errors",
                "errors": {
                    "submission": f"Error: {str(e)}"
                }
            }

    def _get_workspace_users(self) -> List[Dict[str, Any]]:
        """Get a list of users in the workspace for the dropdown."""
        try:
            response = self.client.users_list()
            if response["ok"]:
                # Filter out bots and inactive users
                users = [
                    {
                        "text": {"type": "plain_text", "text": user.get("real_name", user["name"]), "emoji": True},
                        "value": user["id"]
                    }
                    for user in response["members"]
                    if not user.get("is_bot", False) and not user.get("deleted", False)
                ]
                return users
            return []
        except SlackApiError as e:
            logger.error(f"Error fetching workspace users: {e}")
            return [] 