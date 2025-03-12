from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import logging

logger = logging.getLogger(__name__)

class SlackCommandsHandler:
    def __init__(self, slack_client: WebClient):
        self.client = slack_client

    def handle_command(self, form_data):
        """Handle incoming Slack slash commands"""
        command = form_data.get('command')
        user_id = form_data.get('user_id')
        trigger_id = form_data.get('trigger_id')
        
        if command != '/leave':
            return {"ok": False, "error": "Invalid command"}
            
        try:
            # Open a modal for leave request
            self.client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "leave_request_modal",
                    "title": {"type": "plain_text", "text": "Leave Request"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "leave_type",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select leave type"
                                },
                                "options": [
                                    {
                                        "text": {"type": "plain_text", "text": "Vacation"},
                                        "value": "vacation"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "Sick Leave"},
                                        "value": "sick"
                                    },
                                    {
                                        "text": {"type": "plain_text", "text": "Personal"},
                                        "value": "personal"
                                    }
                                ],
                                "action_id": "leave_type_select"
                            },
                            "label": {"type": "plain_text", "text": "Leave Type"}
                        },
                        {
                            "type": "input",
                            "block_id": "date_range",
                            "element": {
                                "type": "datepicker",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a date"
                                },
                                "action_id": "start_date"
                            },
                            "label": {"type": "plain_text", "text": "Start Date"}
                        },
                        {
                            "type": "input",
                            "block_id": "end_date",
                            "element": {
                                "type": "datepicker",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select a date"
                                },
                                "action_id": "end_date"
                            },
                            "label": {"type": "plain_text", "text": "End Date"}
                        },
                        {
                            "type": "input",
                            "block_id": "reason",
                            "element": {
                                "type": "plain_text_input",
                                "multiline": True,
                                "action_id": "reason_text"
                            },
                            "label": {"type": "plain_text", "text": "Reason"}
                        }
                    ]
                }
            )
            return {"ok": True}
            
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e.response['error']}")
            return {"ok": False, "error": "Failed to open leave request form"} 