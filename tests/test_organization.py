"""
Tests for the organization configuration module.
"""
import pytest
from src.config.organization import (
    is_department_head,
    get_department_head,
    get_department_name,
    HR_CHANNEL_ID,
    DEPARTMENTS
)

@pytest.fixture
def mock_department_structure(monkeypatch):
    """Fixture to mock the department structure for testing."""
    test_departments = {
        "Engineering": {
            "head": "D123",
            "members": ["M456", "M789"]
        },
        "Human Resources": {
            "head": "U06PNMDFVQW",
            "members": ["U06PNMDFVQW", "U07UV1KFBR7"]
        }
    }
    monkeypatch.setattr("src.config.organization.DEPARTMENTS", test_departments)
    return test_departments

def test_is_department_head(mock_department_structure):
    """Test department head identification."""
    assert is_department_head("D123") is True
    assert is_department_head("U06PNMDFVQW") is True
    assert is_department_head("M456") is False
    assert is_department_head("U07UV1KFBR7") is False

def test_get_department_head(mock_department_structure):
    """Test getting department head for team members."""
    assert get_department_head("M456") == "D123"
    assert get_department_head("M789") == "D123"
    assert get_department_head("U07UV1KFBR7") == "U06PNMDFVQW"
    assert get_department_head("D123") is None  # Department head has no head

def test_get_department_name(mock_department_structure):
    """Test getting department name for users."""
    assert get_department_name("D123") == "Engineering"
    assert get_department_name("U06PNMDFVQW") == "Human Resources"
    assert get_department_name("M456") == "Engineering"
    assert get_department_name("U07UV1KFBR7") == "Human Resources"
    assert get_department_name("UNKNOWN") is None

def test_hr_channel_id():
    """Test HR channel ID constant."""
    assert HR_CHANNEL_ID == "#leave-requests"

def test_get_department_head_with_self_as_team_member():
    """Test that department heads can approve requests from their team members, even if listed as team members themselves."""
    # Test case: Dabyll (U06PNMDFVQW) is both department head and team member
    # Nikko (U07UV1KFBR7) is a team member
    dept_head_id = get_department_head("U07UV1KFBR7")
    assert dept_head_id == "U06PNMDFVQW", "Department head should be found even if they are listed as a team member" 