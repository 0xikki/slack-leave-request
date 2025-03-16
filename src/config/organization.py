"""
Organization configuration module.
"""

import os
import json
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Department structure
DEPARTMENTS = {
    "Engineering": {
        "head": "D123",
        "members": ["M456", "M789"]
    },
    "Human Resources": {
        "head": "U06PNMDFVQW",
        "members": ["U06PNMDFVQW", "U07UV1KFBR7"]  # Department head can also be a team member
    },
    "Development and Architecture": {
        "head": "U06M5QCCLN9",  # 0xikki
        "members": ["U06MKKWAWJX", "U06M5QCCLN9"]  # Kuro and 0xikki
    },
    "HR Team": {
        "head": "U06PNMDFVQW",  # Dabyll
        "members": ["U07UV1KFBR7", "U06PNMDFVQW"]  # Nikko and Dabyll
    },
    "Socials": {
        "head": "U06MM2BKMM2",  # Gabe
        "members": ["U234567", "U345678", "U456789", "U06MM2BKMM2"]
    }
}

# Set of all department heads
DEPARTMENT_HEADS = {dept_info["head"] for dept_info in DEPARTMENTS.values()}

def load_admin_users() -> List[str]:
    """Load admin user IDs."""
    # Super admins have full access to all actions
    SUPER_ADMINS = ["U06M5QCCLN9"]  # 0xikki
    # Regular admins (HR team)
    HR_ADMINS = ["U06PNMDFVQW"]  # Dabyll
    
    return SUPER_ADMINS + HR_ADMINS

def is_department_head(user_id: str) -> bool:
    """Check if user is a department head."""
    return user_id in DEPARTMENT_HEADS

def get_department_head(user_id: str) -> Optional[str]:
    """Get department head for a user."""
    # If user is a department head, they report to HR
    if user_id in DEPARTMENT_HEADS:
        return None
        
    # Look for user in department members
    for dept_info in DEPARTMENTS.values():
        if user_id in dept_info["members"]:
            return dept_info["head"]
    return None

def get_department_name(user_id: str) -> Optional[str]:
    """Get department name for a user."""
    for dept_name, dept_info in DEPARTMENTS.items():
        if user_id in dept_info["members"] or user_id == dept_info["head"]:
            return dept_name
    return None

# Load admin users
ADMIN_USERS = load_admin_users()

# For testing purposes, add some default admin users if list is empty
if not ADMIN_USERS:
    logger.warning("No admin users found, using default")
    ADMIN_USERS = ["U06PNMDFVQW"]  # Default admin user

# Channel ID for HR - use environment variable with fallback
HR_CHANNEL_ID = os.getenv("SLACK_ADMIN_CHANNEL")  # Use the channel ID from .env
if not HR_CHANNEL_ID:
    logger.error("SLACK_ADMIN_CHANNEL not set in environment variables")
    HR_CHANNEL_ID = "C06SEP5F276"  # Fallback to default channel

# Dictionary mapping department heads to their department and team members
DEPARTMENT_STRUCTURE = {
    # Socials Department
    "U06MM2BKMM2": {  # Gabe
        "department": "Socials",
        "team_members": [
            "U234567",  # Replace with actual Slack user IDs
            "U345678",
            "U456789"
        ]
    },
    
    # Development and Architecture Department
    "U06M5QCCLN9": {  #0xikki
        "department": "Development and Architecture",
        "team_members": [
            "U06MKKWAWJX" #Kuro
        ]
    },
    
    # Human Resources Department
    "U06PNMDFVQW": {  # Dabyll - head
        "department": "HR",
        "team_members": [
            "U07UV1KFBR7", #Nikko - member
            "U333444",
            "U444555"
        ]
    },
    
    # Sales Department
    "U555666": {  # Replace with actual Slack user ID of Sales Head
        "department": "Sales",
        "team_members": [
            "U666777",
            "U777888",
            "U888999"
        ]
    }
} 