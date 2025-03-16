import requests
import time
import json
import hmac
import hashlib
from urllib.parse import urlencode
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

BASE_URL = 'http://localhost:5000'
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET', '')

def get_slack_signature(timestamp, body):
    """Generate a valid Slack signature for testing"""
    sig_basestring = f'v0:{timestamp}:{body}'
    signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_timeoff_command():
    """Test the /slack/commands endpoint with /timeoff command"""
    timestamp = str(int(time.time()))
    data = {
        'command': '/timeoff',
        'user_id': 'U123456',
        'trigger_id': 'test_trigger'
    }
    body = urlencode(data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': get_slack_signature(timestamp, body)
    }
    response = requests.post(f'{BASE_URL}/slack/commands', headers=headers, data=data)
    print('\nTesting /timeoff command:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')

def test_modal_submission():
    """Test the /slack/interactivity endpoint with modal submission"""
    timestamp = str(int(time.time()))
    payload = {
        'type': 'view_submission',
        'user': {'id': 'U123456'},
        'view': {
            'callback_id': 'leave_request',
            'state': {
                'values': {
                    'leave_type_block': {
                        'leave_type_select': {
                            'type': 'static_select',
                            'selected_option': {
                                'value': 'PTO',
                                'text': {'type': 'plain_text', 'text': 'PTO', 'emoji': True}
                            }
                        }
                    },
                    'start_date_block': {
                        'start_date_select': {
                            'type': 'datepicker',
                            'selected_date': '2024-03-20'
                        }
                    },
                    'end_date_block': {
                        'end_date_select': {
                            'type': 'datepicker',
                            'selected_date': '2024-03-21'
                        }
                    },
                    'coverage_block': {
                        'coverage_select': {
                            'type': 'users_select',
                            'selected_user': 'U789012'
                        }
                    },
                    'tasks_block': {
                        'tasks_input': {
                            'type': 'plain_text_input',
                            'value': 'Code review and daily standup'
                        }
                    },
                    'reason_block': {
                        'reason_input': {
                            'type': 'plain_text_input',
                            'value': 'Taking some time off'
                        }
                    }
                }
            }
        }
    }
    data = {
        'payload': json.dumps(payload)
    }
    body = urlencode(data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': get_slack_signature(timestamp, body)
    }
    response = requests.post(f'{BASE_URL}/slack/interactivity', headers=headers, data=data)
    print('\nTesting modal submission:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')

def test_url_verification():
    """Test the /slack/events endpoint with URL verification"""
    timestamp = str(int(time.time()))
    data = {
        'type': 'url_verification',
        'challenge': 'test_challenge'
    }
    body = json.dumps(data)
    headers = {
        'Content-Type': 'application/json',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': get_slack_signature(timestamp, body)
    }
    response = requests.post(f'{BASE_URL}/slack/events', headers=headers, json=data)
    print('\nTesting URL verification:')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')

if __name__ == '__main__':
    test_timeoff_command()
    test_modal_submission()
    test_url_verification() 