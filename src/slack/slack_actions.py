"""
Handles Slack interactive actions for leave request approvals/denials.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import logging
import os
from typing import Dict, List, Any, Optional
from src.config.organization import (
    is_department_head,
    get_department_head,
    get_department_name,
    HR_CHANNEL_ID,
    ADMIN_USERS,
    load_admin_users
)
import re
from src.slack.helpers import create_admin_notification_blocks, create_user_notification_blocks, create_denial_modal_view

logger = logging.getLogger(__name__)

class SlackActionsHandler:
    def __init__(self, client: WebClient):
        self.client = client
        self.logger = logging.getLogger(__name__)

    def handle_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack interactive actions."""
        try:
            # Check payload type first
            payload_type = payload.get("type")
            logger.info(f"Handling action of type: {payload_type}")
            logger.info(f"Full payload: {json.dumps(payload)}")

            if payload_type == "view_submission":
                # Handle view submissions
                return self.handle_view_submission(payload)
            elif payload_type == "block_actions":
                # Handle button clicks
                action = payload.get("actions", [{}])[0]
                action_id = action.get("action_id")
                user_id = payload.get("user", {}).get("id")
                
                logger.info(f"Handling block action {action_id} from user {user_id}")

                if not action_id or not user_id:
                    logger.error("Missing action_id or user_id")
                    return {
                        "response_action": "errors",
                        "errors": {"action": "Invalid action"}
                    }

                # Get container info first
                container = payload.get("container", {})
                channel_id = container.get("channel_id")
                message_ts = container.get("message_ts")

                if not channel_id or not message_ts:
                    logger.error(f"Missing container info: channel_id={channel_id}, message_ts={message_ts}")
                    return {
                        "response_action": "errors",
                        "errors": {"action": "Could not extract request details"}
                    }

                # Extract request details from message
                message = payload.get("message", {})
                if not message:
                    logger.error("No message found in payload")
                    return {
                        "response_action": "errors",
                        "errors": {"action": "Could not extract request details"}
                    }

                # Add container info to message for _extract_request_details
                message["container"] = container

                request_details = self._extract_request_details(message)
                if not request_details:
                    logger.error("Could not extract request details from message")
                    return {
                        "response_action": "errors",
                        "errors": {"action": "Could not extract request details"}
                    }

                # Check authorization
                requester_id = request_details.get("requester_id")
                if user_id == requester_id:
                    # Check if user is super admin
                    admin_users = load_admin_users()
                    logger.info(f"User {user_id} is trying to handle their own request. Admin users: {admin_users}")
                    if user_id not in admin_users:
                        logger.error(f"User {user_id} tried to handle their own request but is not an admin")
                        return {
                            "response_action": "errors",
                            "errors": {"action": "You cannot approve or reject your own request"}
                        }

                if not self._is_authorized(user_id, requester_id):
                    logger.error(f"User {user_id} is not authorized to perform this action")
                    return {
                        "response_action": "errors",
                        "errors": {"action": "You are not authorized to perform this action"}
                    }

                # Handle different actions
                try:
                    if action_id == "approve_leave":
                        logger.info(f"Processing approval from user {user_id}")
                        # Process approval immediately
                        if not self._handle_approval(payload, request_details):
                            return {
                                "response_action": "errors",
                                "errors": {"action": "An error occurred while processing your request"}
                            }
                        # Return empty response to acknowledge
                        return {"response_action": "clear"}

                    elif action_id == "reject_leave":
                        if not payload.get("trigger_id"):
                            logger.error("Missing trigger_id for rejection modal")
                            return {
                                "response_action": "errors",
                                "errors": {"action": "Could not open rejection modal"}
                            }

                        # Extract request details from message
                        message = payload.get("message", {})
                        # Add container info to message for _extract_request_details
                        message["container"] = payload.get("container", {})
                        
                        request_details = self._extract_request_details(message)
                        if not request_details:
                            logger.error("Could not extract request details from message")
                            return {
                                "response_action": "errors",
                                "errors": {"action": "Could not extract request details"}
                            }

                        # Create leave request object for modal
                        leave_request = {
                            "user": {"id": request_details["requester_id"]},
                            "channel_id": request_details["channel_id"],
                            "message_ts": request_details["message_ts"],
                            "leave_type": request_details["leave_type"],
                            "start_date": request_details["start_date"],
                            "end_date": request_details["end_date"]
                        }

                        # Create and open the rejection modal
                        try:
                            modal_view = create_denial_modal_view(leave_request)
                            logger.info(f"Opening modal with view: {json.dumps(modal_view)}")
                            response = self.client.views_open(
                                trigger_id=payload["trigger_id"],
                                view=modal_view
                            )
                            logger.info(f"Modal open response: {json.dumps(response)}")
                            return {"response_action": "clear"}
                        except Exception as e:
                            logger.error(f"Error opening rejection modal: {str(e)}", exc_info=True)
                            return {
                                "response_action": "errors",
                                "errors": {"action": "Could not open rejection modal"}
                            }

                    else:
                        logger.error(f"Invalid action_id: {action_id}")
                        return {
                            "response_action": "errors",
                            "errors": {"action": "Invalid action"}
                        }

                except Exception as e:
                    logger.error(f"Error processing action: {str(e)}", exc_info=True)
                    return {
                        "response_action": "errors",
                        "errors": {"action": "An error occurred while processing your request"}
                    }

            else:
                logger.error(f"Invalid payload type: {payload_type}")
                return {
                    "response_action": "errors",
                    "errors": {"action": "Invalid payload type"}
                }

        except Exception as e:
            logger.error(f"Error handling action: {str(e)}", exc_info=True)
            return {
                "response_action": "errors",
                "errors": {"action": "An error occurred while processing your request"}
            }

    def handle_view_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle view submission."""
        try:
            view = payload.get("view", {})
            callback_id = view.get("callback_id")
            
            logger.info(f"Handling view submission with callback_id: {callback_id}")
            
            # Check if this is a denial reason submission
            if callback_id == "denial_modal":
                values = view.get("state", {}).get("values", {})
                metadata_str = view.get("private_metadata", "{}")
                
                try:
                    metadata = json.loads(metadata_str)
                    logger.info(f"Decoded metadata: {json.dumps(metadata)}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode metadata: {str(e)}")
                    return {
                        "response_action": "errors",
                        "errors": {
                            "denial_reason": "Invalid request data. Please try again."
                        }
                    }

                # Extract and validate denial reason
                denial_reason = values.get("denial_reason", {}).get("denial_reason_input", {}).get("value")
                if not denial_reason:
                    logger.error("Missing denial reason")
                    return {
                        "response_action": "errors",
                        "errors": {
                            "denial_reason": "Please provide a reason for rejection"
                        }
                    }

                # Validate required metadata
                required_fields = ["requester_id", "channel_id", "message_ts"]
                missing_fields = [field for field in required_fields if not metadata.get(field)]
                if missing_fields:
                    logger.error(f"Missing metadata fields: {missing_fields}")
                    return {
                        "response_action": "errors",
                        "errors": {
                            "denial_reason": "Invalid request data. Please try again."
                        }
                    }

                try:
                    # Update original message in channel
                    channel_id = metadata["channel_id"]
                    message_ts = metadata["message_ts"]
                    requester_id = metadata["requester_id"]
                    leave_type = metadata.get("leave_type", "leave")
                    start_date = metadata.get("start_date", "")
                    end_date = metadata.get("end_date", start_date)

                    # Update the original message first
                    self.client.chat_update(
                        channel=channel_id,
                        ts=message_ts,
                        text=f"Leave request from <@{requester_id}> was rejected",
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f":x: Leave request from <@{requester_id}> was rejected\n*Reason:* {denial_reason}"
                                }
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                    {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"}
                                ]
                            }
                        ]
                    )

                    # Send DM to requester
                    try:
                        # Open DM channel first
                        dm_open = self.client.conversations_open(users=[requester_id])
                        dm_channel = dm_open["channel"]["id"]
                        
                        self.client.chat_postMessage(
                            channel=dm_channel,
                            text=f"Your {leave_type} request was rejected",
                            blocks=[
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f":x: Your {leave_type} request was rejected\n*Reason:* {denial_reason}"
                                    }
                                },
                                {
                                    "type": "section",
                                    "fields": [
                                        {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                        {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"}
                                    ]
                                }
                            ]
                        )
                    except SlackApiError as e:
                        logger.error(f"Failed to send DM: {str(e)}")
                        # Continue even if DM fails
                    
                    # Return empty response to close modal
                    return {}

                except SlackApiError as e:
                    logger.error(f"Slack API error: {str(e)}")
                    return {
                        "response_action": "errors",
                        "errors": {
                            "denial_reason": "Failed to process rejection. Please try again."
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing rejection: {str(e)}", exc_info=True)
                    return {
                        "response_action": "errors",
                        "errors": {
                            "denial_reason": "An error occurred. Please try again."
                        }
                    }

            elif callback_id == "leave_request_modal":
                # Extract form values from state
                state_values = view.get("state", {}).get("values", {})
                
                # Validate required fields
                errors = {}
                
                # Validate leave type
                leave_type_values = state_values.get("leave_type_block", {}).get("leave_type", {})
                if not leave_type_values.get("selected_option"):
                    errors["leave_type_block"] = "Please select a leave type"
                
                # Validate start date
                start_date = state_values.get("date_block", {}).get("start_date", {}).get("selected_date")
                if not start_date:
                    errors["date_block"] = "Please select a start date"
                
                # Validate end date
                end_date = state_values.get("end_date_block", {}).get("end_date", {}).get("selected_date")
                if not end_date:
                    errors["end_date_block"] = "Please select an end date"
                
                # Validate coverage person
                coverage_person = state_values.get("coverage_block", {}).get("coverage_person", {}).get("selected_user")
                if not coverage_person:
                    errors["coverage_block"] = "Please select who will cover for you"
                
                # Validate tasks
                tasks = state_values.get("tasks_block", {}).get("tasks", {}).get("value")
                if not tasks:
                    errors["tasks_block"] = "Please list tasks to be covered"
                
                # Validate reason
                reason = state_values.get("reason_block", {}).get("reason", {}).get("value")
                if not reason:
                    errors["reason_block"] = "Please provide a reason"
                
                if errors:
                    return {
                        "response_action": "errors",
                        "errors": errors
                    }
                
                try:
                    # Get user info
                    user = payload.get("user", {})
                    user_id = user.get("id")
                    
                    # Get leave type display text
                    leave_type_option = leave_type_values.get("selected_option", {})
                    leave_type = leave_type_option.get("value")
                    leave_type_display = leave_type_option.get("text", {}).get("text", leave_type)
                    
                    # Create notification blocks
                    notification_blocks = [
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Requester:*\n<@{user_id}>"},
                                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type_display}"},
                                {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"},
                                {"type": "mrkdwn", "text": f"*Coverage:*\n<@{coverage_person}>"}
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Tasks:*\n{tasks}"},
                                {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"}
                            ]
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
                                    "action_id": "approve_leave"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "❌ Reject",
                                        "emoji": True
                                    },
                                    "style": "danger",
                                    "action_id": "reject_leave"
                                }
                            ]
                        }
                    ]
                    
                    # Send confirmation to user
                    try:
                        self.client.chat_postMessage(
                            channel=user_id,
                            text=f"Your {leave_type_display} request has been submitted",
                            blocks=notification_blocks[:-1] + [{
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        "text": ":information_source: Your request has been submitted and is pending approval."
                                    }
                                ]
                            }]
                        )
                    except SlackApiError as e:
                        logger.error(f"Failed to send confirmation to user: {str(e)}")
                        # Continue even if confirmation fails
                    
                    # Check if user is department head
                    if is_department_head(user_id):
                        # If user is department head, send directly to HR
                        if HR_CHANNEL_ID:
                            try:
                                self.client.chat_postMessage(
                                    channel=HR_CHANNEL_ID,
                                    text=f"New {leave_type_display} request from Department Head <@{user_id}>",
                                    blocks=notification_blocks
                                )
                            except SlackApiError as e:
                                logger.error(f"Failed to send to HR channel: {str(e)}")
                    else:
                        # Get department head
                        dept_head = get_department_head(user_id)
                        if dept_head:
                            try:
                                self.client.chat_postMessage(
                                    channel=dept_head,
                                    text=f"New {leave_type_display} request from <@{user_id}>",
                                    blocks=notification_blocks
                                )
                            except SlackApiError as e:
                                logger.error(f"Failed to send to department head: {str(e)}")
                        elif HR_CHANNEL_ID:
                            try:
                                self.client.chat_postMessage(
                                    channel=HR_CHANNEL_ID,
                                    text=f"New {leave_type_display} request from <@{user_id}> (No department head found)",
                                    blocks=notification_blocks
                                )
                            except SlackApiError as e:
                                logger.error(f"Failed to send to HR channel: {str(e)}")
                    
                    # Return empty response to close modal
                    return {}
                    
                except Exception as e:
                    logger.error(f"Error processing leave request: {str(e)}", exc_info=True)
                    return {
                        "response_action": "errors",
                        "errors": {
                            "submission": "Failed to process request. Please try again."
                        }
                    }
            
            # For any other modal, just close it
            return {}
            
        except Exception as e:
            logger.error(f"Error handling view submission: {str(e)}", exc_info=True)
            return {
                "response_action": "errors",
                "errors": {
                    "submission": "An unexpected error occurred. Please try again."
                }
            }

    def _validate_leave_request(self, values: Dict[str, Any]) -> Optional[Dict[str, Dict[str, str]]]:
        """Validate leave request form values."""
        errors = {}
        
        # Validate leave type
        leave_type_block = values.get("leave_type_block", {})
        if not leave_type_block.get("leave_type", {}).get("selected_option", {}).get("value"):
            errors["leave_type_block"] = "Please select a leave type"
        
        # Validate dates
        date_block = values.get("date_block", {})
        if not date_block.get("start_date", {}).get("selected_date"):
            errors["date_block"] = "Please select a start date"
        
        # Validate coverage
        coverage_block = values.get("coverage_block", {})
        if not coverage_block.get("coverage_person", {}).get("selected_user"):
            errors["coverage_block"] = "Please select who will cover for you"
        
        # Validate tasks
        tasks_block = values.get("tasks_block", {})
        if not tasks_block.get("tasks", {}).get("value"):
            errors["tasks_block"] = "Please list tasks to be covered"
        
        # Validate reason
        reason_block = values.get("reason_block", {})
        if not reason_block.get("reason", {}).get("value"):
            errors["reason_block"] = "Please provide a reason"
        
        return errors if errors else None

    def _queue_leave_request_processing(self, payload: Dict[str, Any]) -> None:
        """Queue leave request processing to be handled asynchronously."""
        import threading
        thread = threading.Thread(target=self._process_leave_request, args=(payload,))
        thread.daemon = True
        thread.start()

    def _process_leave_request(self, payload: Dict[str, Any]) -> None:
        """Process leave request in background."""
        try:
            view = payload.get("view", {})
            user = payload.get("user", {})
            values = view.get("state", {}).get("values", {})
            
            # Extract form values
            leave_type_option = values.get("leave_type_block", {}).get("leave_type", {}).get("selected_option", {})
            leave_type = leave_type_option.get("value")
            leave_type_display = leave_type_option.get("text", {}).get("text", leave_type)
            start_date = values.get("date_block", {}).get("start_date", {}).get("selected_date")
            coverage_person = values.get("coverage_block", {}).get("coverage_person", {}).get("selected_user")
            tasks = values.get("tasks_block", {}).get("tasks", {}).get("value")
            reason = values.get("reason_block", {}).get("reason", {}).get("value")
            
            logger.info(f"Processing leave request for user {user.get('id')} of type {leave_type_display}")
            
            # Create notification blocks with approval/rejection buttons
            notification_blocks = [
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Requester:*\n<@{user.get('id')}>"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{leave_type_display}"},
                        {"type": "mrkdwn", "text": f"*Start Date:*\n{start_date}"},
                        {"type": "mrkdwn", "text": f"*Coverage:*\n<@{coverage_person}>"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Tasks to Cover:*\n{tasks}"},
                        {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"}
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "actions",
                    "block_id": "leave_request_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve Request",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": json.dumps({
                                "request_id": f"{user.get('id')}_{start_date}_{leave_type}",
                                "action": "approve"
                            }),
                            "action_id": "approve_leave",
                            "confirm": {
                                "title": {
                                    "type": "plain_text",
                                    "text": "Approve Leave Request"
                                },
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"Are you sure you want to approve this {leave_type_display} request from <@{user.get('id')}>?"
                                },
                                "confirm": {
                                    "type": "plain_text",
                                    "text": "Yes, Approve"
                                },
                                "deny": {
                                    "type": "plain_text",
                                    "text": "No, Cancel"
                                },
                                "style": "primary"
                            }
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Reject Request",
                                "emoji": True
                            },
                            "style": "danger",
                            "value": json.dumps({
                                "request_id": f"{user.get('id')}_{start_date}_{leave_type}",
                                "action": "reject"
                            }),
                            "action_id": "reject_leave",
                            "confirm": {
                                "title": {
                                    "type": "plain_text",
                                    "text": "Reject Leave Request"
                                },
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"Are you sure you want to reject this {leave_type_display} request from <@{user.get('id')}>?\nThis will open a dialog to provide a rejection reason."
                                },
                                "confirm": {
                                    "type": "plain_text",
                                    "text": "Yes, Reject"
                                },
                                "deny": {
                                    "type": "plain_text",
                                    "text": "No, Cancel"
                                },
                                "style": "danger"
                            }
                        }
                    ]
                }
            ]
            
            # Send confirmation to user
            user_blocks = notification_blocks[:-1]  # Remove action buttons for user notification
            user_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":information_source: Your request has been submitted and is pending approval."
                    }
                ]
            })
            
            try:
                self.client.chat_postMessage(
                    channel=user.get("id"),
                    text=f"Your {leave_type_display} request has been submitted",
                    blocks=user_blocks
                )
                logger.info(f"Sent confirmation to user {user.get('id')}")
            except SlackApiError as e:
                logger.error(f"Failed to send confirmation to user: {str(e)}")
                raise
            
            # Check if user is department head
            user_id = user.get("id")
            logger.info(f"Checking if user {user_id} is department head")
            
            if is_department_head(user_id):
                logger.info(f"User {user_id} is department head, sending to HR channel {HR_CHANNEL_ID}")
                # If user is department head, send directly to HR
                if HR_CHANNEL_ID:
                    try:
                        self.client.chat_postMessage(
                            channel=HR_CHANNEL_ID,
                            text=f"New {leave_type_display} request from Department Head <@{user_id}>",
                            blocks=notification_blocks
                        )
                        logger.info(f"Successfully sent request to HR channel {HR_CHANNEL_ID}")
                    except SlackApiError as e:
                        logger.error(f"Failed to send to HR channel: {str(e)}")
                        # Don't raise here - we've already confirmed to the user
                else:
                    logger.error("HR_CHANNEL_ID not configured")
            else:
                # Get department head for the user
                dept_head = get_department_head(user_id)
                if dept_head:
                    logger.info(f"Sending request to department head {dept_head}")
                    try:
                        self.client.chat_postMessage(
                            channel=dept_head,
                            text=f"New {leave_type_display} request from <@{user_id}>",
                            blocks=notification_blocks
                        )
                        logger.info(f"Successfully sent request to department head {dept_head}")
                    except SlackApiError as e:
                        logger.error(f"Failed to send to department head: {str(e)}")
                        # Don't raise here - we've already confirmed to the user
                else:
                    logger.info(f"No department head found for user {user_id}, sending to HR")
                    if HR_CHANNEL_ID:
                        try:
                            self.client.chat_postMessage(
                                channel=HR_CHANNEL_ID,
                                text=f"New {leave_type_display} request from <@{user_id}> (No department head found)",
                                blocks=notification_blocks
                            )
                            logger.info(f"Successfully sent request to HR channel {HR_CHANNEL_ID}")
                        except SlackApiError as e:
                            logger.error(f"Failed to send to HR channel: {str(e)}")
                            # Don't raise here - we've already confirmed to the user
                    else:
                        logger.error("HR_CHANNEL_ID not configured")
                
        except Exception as e:
            logger.error(f"Error processing leave request: {str(e)}", exc_info=True)
            # Try to notify user of error
            try:
                self.client.chat_postMessage(
                    channel=user.get("id"),
                    text="There was an error processing your leave request. Please contact HR or try again."
                )
            except:
                logger.error("Failed to send error notification to user", exc_info=True)

    def _queue_rejection_processing(self, payload: Dict[str, Any]) -> None:
        """Queue rejection processing to be handled asynchronously."""
        import threading
        thread = threading.Thread(target=self._process_rejection, args=(payload,))
        thread.daemon = True
        thread.start()

    def _process_rejection(self, payload: Dict[str, Any]) -> None:
        """Process rejection in background."""
        requester_id = None
        try:
            view = payload.get("view", {})
            values = view.get("state", {}).get("values", {})
            
            # Get private metadata
            try:
                metadata_str = view.get("private_metadata", "{}")
                logger.info(f"Processing rejection with metadata string: {metadata_str}")
                metadata = json.loads(metadata_str)
                logger.info(f"Decoded metadata: {json.dumps(metadata)}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode private metadata: {str(e)}")
                raise ValueError("Invalid metadata format")
            
            # Extract rejection reason using the block and action IDs
            denial_reason = values.get("denial_reason", {}).get("denial_reason_input", {}).get("value")
            if not denial_reason:
                raise ValueError("Missing denial reason")
            
            # Extract metadata
            channel_id = metadata.get("channel_id")
            message_ts = metadata.get("message_ts")
            requester_id = metadata.get("requester_id")
            leave_type = metadata.get("leave_type")
            start_date = metadata.get("start_date")
            end_date = metadata.get("end_date", start_date)  # Default to start_date if no end_date
            
            if not all([channel_id, message_ts, requester_id]):
                missing = [k for k, v in {'channel_id': channel_id, 'message_ts': message_ts, 'requester_id': requester_id}.items() if not v]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            logger.info(f"Processing rejection for user {requester_id} in channel {channel_id}")
            
            # Update original message
            try:
                update_response = self.client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    text=f"Leave request from <@{requester_id}> was rejected",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f":x: Leave request from <@{requester_id}> was rejected\n*Reason:* {denial_reason}"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"}
                            ]
                        }
                    ]
                )
                logger.info(f"Successfully updated original message: {json.dumps(update_response)}")
            except SlackApiError as e:
                logger.error(f"Failed to update original message: {str(e)}")
                # Continue to notify user even if update fails
            
            # Notify requester with a single message attempt, similar to approval flow
            try:
                self.client.chat_postMessage(
                    channel=requester_id,
                    text=f"Your {leave_type} request was rejected",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f":x: Your {leave_type} request was rejected\n*Reason:* {denial_reason}"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                {"type": "mrkdwn", "text": f"*Duration:*\n{start_date} to {end_date}"}
                            ]
                        }
                    ]
                )
                logger.info(f"Successfully sent rejection notification to user {requester_id}")
            except SlackApiError as e:
                logger.error(f"Failed to send rejection notification to user {requester_id}: {str(e)}")
                # Don't raise here - we've already updated the original message
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing rejection: {error_msg}", exc_info=True)
            # Only try to send error message if we haven't already tried to send a notification
            if requester_id and "Failed to send rejection notification" not in error_msg:
                try:
                    error_detail = "metadata error" if "metadata" in error_msg.lower() else "processing error"
                    self.client.chat_postMessage(
                        channel=requester_id,
                        text=f"There was an error while processing your leave request rejection. Please try again or contact HR if the issue persists."
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send error notification to user: {str(notify_error)}", exc_info=True)

    def _is_authorized(self, user_id: str, requester_id: str) -> bool:
        """Check if user is authorized to approve/reject the request."""
        # Admin users can approve/reject any request
        if user_id in load_admin_users():
            return True

        # Department heads can approve/reject requests from their team members
        if is_department_head(user_id):
            return True

        return False

    def _extract_request_details(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request details from message blocks."""
        try:
            logger.info(f"Extracting request details from message: {json.dumps(message)}")
            
            # Get channel ID from container or message
            channel_id = message.get("channel_id")  # Try direct channel_id first
            if not channel_id:
                # Try container path from the payload
                container = message.get("container", {})
                channel_id = container.get("channel_id")
                logger.info(f"Found channel_id from container: {channel_id}")
            
            if not channel_id:
                logger.error("Could not find channel_id in message or container")
                return None

            # Get message timestamp
            message_ts = message.get("ts")  # Try direct ts first
            if not message_ts:
                # Try container path
                container = message.get("container", {})
                message_ts = container.get("message_ts")
                logger.info(f"Found message_ts from container: {message_ts}")

            if not message_ts:
                logger.error("Could not find message_ts in message or container")
                return None

            # Extract fields from blocks
            blocks = message.get("blocks", [])
            if not blocks:
                logger.error("No blocks found in message")
                return None

            # First block should contain the requester, type, duration, and coverage
            first_block = next((b for b in blocks if b.get("type") == "section" and b.get("fields")), None)
            if not first_block:
                logger.error("Could not find section block with fields")
                return None

            fields = first_block.get("fields", [])
            logger.info(f"Found fields in first block: {json.dumps(fields)}")
            
            if len(fields) < 4:  # We expect 4 fields (requester, type, duration, coverage)
                logger.error(f"Not enough fields in block: {json.dumps(fields)}")
                return None

            # Extract requester ID from the first field
            requester_text = fields[0].get("text", "")
            requester_match = re.search(r"<@([^>]+)>", requester_text)
            if not requester_match:
                logger.error(f"Could not extract requester ID from text: {requester_text}")
                return None
            
            requester_id = requester_match.group(1)
            logger.info(f"Extracted requester_id: {requester_id}")

            # Extract leave type from the second field
            leave_type_text = fields[1].get("text", "")
            leave_type = leave_type_text.split("*Type:*\n")[-1] if "*Type:*\n" in leave_type_text else ""
            logger.info(f"Extracted leave_type: {leave_type}")

            # Extract duration from the third field
            duration_text = fields[2].get("text", "")
            duration = duration_text.split("*Duration:*\n")[-1] if "*Duration:*\n" in duration_text else ""
            start_date, end_date = duration.split(" to ") if " to " in duration else (duration, duration)
            logger.info(f"Extracted duration - start_date: {start_date}, end_date: {end_date}")

            details = {
                "requester_id": requester_id,
                "channel_id": channel_id,
                "message_ts": message_ts,
                "leave_type": leave_type,
                "start_date": start_date,
                "end_date": end_date
            }
            
            logger.info(f"Successfully extracted request details: {json.dumps(details)}")
            return details

        except Exception as e:
            logger.error(f"Error extracting request details: {str(e)}", exc_info=True)
            return None

    def _queue_approval_processing(self, payload: Dict[str, Any], request_details: Dict[str, Any]) -> None:
        """Queue approval processing to be handled asynchronously."""
        import threading
        thread = threading.Thread(target=self._handle_approval, args=(payload, request_details))
        thread.daemon = True
        thread.start()

    def _handle_approval(self, payload: Dict[str, Any], request_details: Dict[str, Any]) -> bool:
        """Handle leave request approval."""
        try:
            channel_id = request_details.get("channel_id")
            message_ts = request_details.get("message_ts")
            user_id = payload.get("user", {}).get("id")
            requester_id = request_details.get("requester_id")
            leave_type = request_details.get("leave_type")

            logger.info(f"Starting approval process with details: channel_id={channel_id}, message_ts={message_ts}, user_id={user_id}, requester_id={requester_id}, leave_type={leave_type}")

            if not all([channel_id, message_ts, user_id, requester_id]):
                missing_fields = [field for field, value in {
                    'channel_id': channel_id,
                    'message_ts': message_ts,
                    'user_id': user_id,
                    'requester_id': requester_id
                }.items() if not value]
                raise ValueError(f"Missing required fields for approval: {', '.join(missing_fields)}")

            # First, update the original message to remove buttons and show approval
            try:
                self.client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    text=f"Leave request from <@{requester_id}> was approved",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f":white_check_mark: Leave request from <@{requester_id}> was approved by <@{user_id}>"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                {"type": "mrkdwn", "text": f"*Start Date:*\n{request_details.get('start_date')}"}
                            ]
                        }
                    ]
                )
                logger.info("Successfully updated original message")
            except SlackApiError as e:
                logger.error(f"Failed to update original message: {str(e.response)}")
                return False

            # Then, send a confirmation to the requester
            try:
                self.client.chat_postMessage(
                    channel=requester_id,
                    text=f"Your {leave_type} request was approved by <@{user_id}>",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f":white_check_mark: Your {leave_type} request was approved by <@{user_id}>"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Type:*\n{leave_type}"},
                                {"type": "mrkdwn", "text": f"*Start Date:*\n{request_details.get('start_date')}"}
                            ]
                        }
                    ]
                )
                logger.info(f"Successfully sent approval notification to user {requester_id}")
            except SlackApiError as e:
                logger.error(f"Failed to send notification to requester: {str(e.response)}")
                # Don't return False here - we've already updated the original message

            return True

        except Exception as e:
            logger.error(f"Error processing approval: {str(e)}", exc_info=True)
            return False