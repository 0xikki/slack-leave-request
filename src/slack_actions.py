import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.slack.helpers import create_user_notification_blocks, create_denial_modal_view

class SlackActionsHandler:
    """Handles Slack interactive actions for leave request approvals/denials."""
    
    def __init__(self):
        """Initialize the handler with Slack credentials."""
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.logger = logging.getLogger(__name__)
    
    def handle_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an action from a Slack interactive message.
        
        Args:
            payload: The Slack action payload
            
        Returns:
            Dict containing the response status and any error messages
        """
        try:
            # Extract action details
            action = payload["actions"][0]
            action_id = action["action_id"]
            
            # Validate action type
            if action_id not in ["approve_leave", "deny_leave"]:
                return {"ok": False, "error": "Invalid action"}
            
            # Validate message content
            if "message" not in payload:
                return {"ok": False, "error": "Missing message content"}
            
            # Extract request details from the message
            request_details = self._extract_request_details(payload["message"]["blocks"])
            
            if action_id == "approve_leave":
                return self._handle_approval(request_details)
            else:  # action_id == "deny_leave"
                return self._handle_denial(request_details, payload.get("trigger_id"))
                
        except KeyError as e:
            self.logger.error(f"Missing required field: {str(e)}")
            return {"ok": False, "error": f"Missing required field: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error handling action: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def handle_denial_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the submission of a denial reason modal.
        
        Args:
            payload: The modal submission payload
            
        Returns:
            Dict containing the response status and any error messages
        """
        try:
            # Extract values from the submission
            values = payload["view"]["state"]["values"]
            denial_reason = values["denial_reason"]["denial_reason_input"]["value"]
            
            # Get the original request details from private_metadata
            request_details = json.loads(payload["view"]["private_metadata"])
            request_details["status"] = "denied"
            request_details["denial_reason"] = denial_reason
            
            # Send notification to the requester
            self.client.chat_postMessage(
                channel=request_details["requester_id"],
                blocks=create_user_notification_blocks(request_details)
            )
            
            return {"ok": True}
            
        except KeyError as e:
            self.logger.error(f"Missing required field: {str(e)}")
            return {"ok": False, "error": f"Missing required field: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error handling denial submission: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def _handle_approval(self, request_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an approval action."""
        try:
            if not request_details.get("requester_id"):
                return {"ok": False, "error": "Missing requester ID"}
            
            request_details["status"] = "approved"
            
            # Send notification to the requester
            self.client.chat_postMessage(
                channel=request_details["requester_id"],
                blocks=create_user_notification_blocks(request_details)
            )
            
            return {"ok": True}
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return {"ok": False, "error": f"Failed to send approval notification: {str(e)}"}
    
    def _handle_denial(self, request_details: Dict[str, Any], trigger_id: str) -> Dict[str, Any]:
        """Handle a denial action by opening a modal for the reason."""
        try:
            if not trigger_id:
                return {"ok": False, "error": "Missing trigger_id"}
            
            if not request_details.get("requester_id"):
                return {"ok": False, "error": "Missing requester ID"}
            
            # Create a user object for the denial modal
            request_details["user"] = {"id": request_details["requester_id"]}
            
            # Open the denial reason modal
            self.client.views_open(
                trigger_id=trigger_id,
                view=create_denial_modal_view(request_details)
            )
            
            return {"ok": True}
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {str(e)}")
            return {"ok": False, "error": f"Failed to open denial modal: {str(e)}"}
    
    def _extract_request_details(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract leave request details from message blocks."""
        request_details = {}
        
        for block in blocks:
            if block["type"] != "section" or "fields" not in block:
                continue
                
            for field in block["fields"]:
                text = field["text"]
                if "*Requester:*" in text:
                    # Extract user ID from <@U123456> format
                    request_details["requester_id"] = text.split("<@")[1].split(">")[0]
                elif "*Type:*" in text:
                    request_details["leave_type"] = text.split("\n")[1]
                elif "*Start Date:*" in text:
                    # Convert formatted date back to YYYY-MM-DD
                    date_str = text.split("\n")[1]
                    date = datetime.strptime(date_str, "%B %d, %Y")
                    request_details["start_date"] = date.strftime("%Y-%m-%d")
                elif "*End Date:*" in text:
                    # Convert formatted date back to YYYY-MM-DD
                    date_str = text.split("\n")[1]
                    date = datetime.strptime(date_str, "%B %d, %Y")
                    request_details["end_date"] = date.strftime("%Y-%m-%d")
        
        return request_details 