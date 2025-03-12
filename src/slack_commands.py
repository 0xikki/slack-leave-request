import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from src.slack.helpers import (
    create_admin_notification_blocks,
    create_user_notification_blocks,
    create_denial_modal_view
)

class SlackCommandHandler:
    """Handles Slack slash commands and their responses."""
    
    def __init__(self):
        """Initialize the handler with Slack credentials."""
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path(__file__).parent.parent / 'templates'
        self.admin_channel = os.getenv('SLACK_ADMIN_CHANNEL', 'leave-requests')
    
    def handle_leave_command(self, user_id: Optional[str], trigger_id: Optional[str]) -> Dict[str, Any]:
        """
        Handle the /leave command by opening a modal for the user.
        
        Args:
            user_id: The Slack user ID of the requester
            trigger_id: The trigger ID from the slash command
            
        Returns:
            Dict containing the response status and any error messages
        """
        if not user_id:
            return {"ok": False, "error": "Invalid user ID"}
        if not trigger_id:
            return {"ok": False, "error": "Invalid trigger ID"}
            
        try:
            # Load modal template
            modal = self._load_modal_template()
            
            # Open the modal
            self.client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            return {"ok": True}
            
        except SlackApiError as e:
            self.logger.error(f"Error opening modal: {e.response['error']}")
            return {"ok": False, "error": f"Failed to open leave request modal: {e.response['error']}"}
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return {"ok": False, "error": "An unexpected error occurred"}
    
    def handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the submission of a leave request modal."""
        try:
            # Extract values from the submission
            values = payload["view"]["state"]["values"]
            user = payload["user"]
            
            # Extract date values
            dates = values.get("leave_dates", {})
            start_date = dates.get("start_date", {}).get("selected_date")
            end_date = dates.get("end_date", {}).get("selected_date")
            
            if not start_date or not end_date:
                return {"ok": False, "error": "Start date and end date are required"}
                
            # Validate dates
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if end < start:
                return {"ok": False, "error": "End date must be after start date"}
            
            # Extract other fields
            leave_type = values.get("leave_type", {}).get("leave_type_select", {}).get("selected_option", {}).get("value")
            reason = values.get("leave_reason", {}).get("reason_text", {}).get("value")
            tasks = values.get("tasks_coverage", {}).get("tasks_text", {}).get("value")
            covering_user_id = values.get("covering_person", {}).get("covering_user_select", {}).get("selected_user")
            
            if not all([leave_type, reason, tasks, covering_user_id]):
                return {"ok": False, "error": "All fields are required"}
            
            # Create leave request object
            leave_request = {
                "user": user,
                "start_date": start_date,
                "end_date": end_date,
                "leave_type": leave_type,
                "reason": reason,
                "tasks_coverage": tasks,
                "covering_user": {"id": covering_user_id}
            }
            
            # Send notification to admin channel
            self.client.chat_postMessage(
                channel=self.admin_channel,
                blocks=create_admin_notification_blocks(leave_request)
            )
            
            return {"ok": True}
            
        except KeyError as e:
            return {"ok": False, "error": f"Missing required field: {str(e)}"}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except SlackApiError as e:
            return {"ok": False, "error": f"Slack API error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error processing modal submission: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def _load_modal_template(self) -> Dict[str, Any]:
        """
        Load the modal template from the templates directory.
        
        Returns:
            Dict containing the modal configuration
        """
        try:
            template_path = self.templates_dir / 'leave_modal.json'
            with open(template_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Modal template not found at {template_path}")
            # Return a basic modal as fallback
            return {
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Submit Leave Request"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Please fill out your leave request details below:"
                        }
                    }
                ]
            }
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing modal template: {str(e)}")
            raise 