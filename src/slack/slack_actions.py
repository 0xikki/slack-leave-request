from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import logging

logger = logging.getLogger(__name__)

class SlackActionsHandler:
    def __init__(self, slack_client: WebClient):
        self.client = slack_client

    def handle_action(self, payload_str):
        """Handle incoming Slack interactive actions"""
        try:
            payload = json.loads(payload_str)
            action_type = payload.get("type")
            
            if action_type == "view_submission":
                return self._handle_view_submission(payload)
                
            return {"ok": True}
            
        except json.JSONDecodeError:
            logger.error("Failed to parse payload JSON")
            return {"ok": False, "error": "Invalid payload format"}
            
        except Exception as e:
            logger.error(f"Error handling action: {str(e)}")
            return {"ok": False, "error": "Internal server error"}

    def _handle_view_submission(self, payload):
        """Handle form submission from modal"""
        try:
            view = payload["view"]
            if view["callback_id"] != "leave_request_modal":
                return {"ok": False, "error": "Invalid modal callback"}
                
            # Extract form values
            values = view["state"]["values"]
            leave_type = values["leave_type"]["leave_type_select"]["selected_option"]["value"]
            start_date = values["date_range"]["start_date"]["selected_date"]
            end_date = values["end_date"]["end_date"]["selected_date"]
            reason = values["reason"]["reason_text"]["value"]
            user_id = payload["user"]["id"]
            
            # Send confirmation message
            self.client.chat_postMessage(
                channel=user_id,
                text=f"Your leave request has been submitted:\nType: {leave_type}\nFrom: {start_date}\nTo: {end_date}\nReason: {reason}"
            )
            
            # Notify approver (you can customize this part)
            approver_channel = "leave-requests"  # Change this to your approval channel
            self.client.chat_postMessage(
                channel=approver_channel,
                text=f"New leave request from <@{user_id}>:",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*New leave request from <@{user_id}>:*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                            {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"},
                            {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"}
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Approve"},
                                "style": "primary",
                                "value": json.dumps({
                                    "user_id": user_id,
                                    "leave_type": leave_type,
                                    "start_date": start_date,
                                    "end_date": end_date
                                }),
                                "action_id": "approve_leave"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Reject"},
                                "style": "danger",
                                "value": json.dumps({
                                    "user_id": user_id,
                                    "leave_type": leave_type,
                                    "start_date": start_date,
                                    "end_date": end_date
                                }),
                                "action_id": "reject_leave"
                            }
                        ]
                    }
                ]
            )
            
            return {"ok": True}
            
        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            return {"ok": False, "error": "Missing required field"}
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"ok": False, "error": "Failed to process leave request"} 