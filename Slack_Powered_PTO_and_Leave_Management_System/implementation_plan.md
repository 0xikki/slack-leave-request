# Implementation plan

## Phase 1: Environment Setup

1.  Create a new project directory (e.g., `slack-leave-system`) and initialize a Git repository with `main` and `dev` branches. (Project Requirements: Overview)
2.  Install the required Python version (use the default system Python, as no explicit version is given) and set up a virtual environment. (Project Requirements: Tech Stack - Backend)
3.  Create a configuration file at `/config/config.json` to store Slack tokens, signing secret, admin Slack user IDs, and admin channel ID. (Project Requirements: Admin Approval Workflow)
4.  Set environment variables for `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and any other secrets. (Project Requirements: Admin Approval Workflow)
5.  Register a new Slack App via the Slack API dashboard and configure the slash command `/leave` with the request URL pointing to your development endpoint (e.g., using ngrok for local testing). (Project Requirements: Slash Command, Frontend/Integration)
6.  **Validation**: Verify the Slack App settings in the dashboard to ensure the slash command configuration is correct.

## Phase 2: Slack UI (Frontend/Integration) Development

1.  Create a file `/templates/leave_modal.json` to define the Block Kit modal UI. (Project Requirements: Modal Interface)

2.  In `/templates/leave_modal.json`, define fields for:

    *   Date(s) of absence (provide single date picker and/or a date range picker if supported)
    *   Reason for leave (plain text input)
    *   Type of leave (static select with options: Sick, Emergency, PTO, Holiday, Offset)
    *   Tasks to be covered (plain text input)
    *   Person who will cover (plain text input)
    *   Supporting document upload (this field can be represented as an optional attachment note if file upload isn’t directly supported)
    *   A note indicating the times displayed are based on UK work hours (9 AM to 5 PM). (Project Requirements: Modal Interface)

3.  Style the modal using Slack’s Aubergine theme options if available. (Project Requirements: Modal Interface)

4.  **Validation**: Use Slack’s Block Kit Builder to preview and verify the layout and functionality of the modal.

## Phase 3: Backend Development

1.  Create the main backend application file `/app.py` using a Python web framework (e.g., Flask) to handle incoming Slack POST events. (Project Requirements: Backend)

2.  In `/app.py`, set up an endpoint (e.g., `/slack/commands`) to receive slash command payloads from Slack. (Project Requirements: Slash Command)

3.  Implement verification of Slack request signatures in the endpoint to ensure secure communication. (Project Requirements: Error Handling)

4.  Within the `/slack/commands` endpoint, parse the `/leave` command payload and trigger the opening of the leave modal using Slack’s `views.open` API call along with the JSON from `/templates/leave_modal.json`. (Project Requirements: Slash Command, Modal Interface)

5.  Create another endpoint at `/slack/interactions` to handle modal submission callbacks. (Project Requirements: Modal Interface)

6.  In `/slack/interactions`, process the modal submission data by extracting the leave request details. (Project Requirements: Modal Interface)

7.  After processing a leave request, post a message to a dedicated Slack channel (e.g., `/slack/admin_notify`) informing admins of the new leave request with Approve and Deny buttons using Block Kit actions. (Project Requirements: Admin Approval Workflow)

8.  Create helper functions in `/slack/helpers.py` for constructing Slack messages and modals to keep the code organized. (Project Requirements: Slack API Integration)

9.  Implement the endpoint `/slack/actions` to handle admin interactions (button clicks) from the leave request notification message. (Project Requirements: Admin Approval Workflow)

10. In `/slack/actions`, branch logic for Approve and Deny actions:

    *   For Approve: Immediately notify the requester of approval.
    *   For Deny: Trigger a modal prompting the admin for a reason, then notify the requester with the denial and reason. (Project Requirements: Admin Approval Workflow)

11. **Validation**: Test the endpoints locally (using ngrok) by simulating slash command payloads and Slack interactivity payloads to ensure correct behavior.

## Phase 4: Integration

1.  Connect the backend endpoints with the Slack App configuration by updating the Request URL for slash commands and interactivity in the Slack dashboard to point to your ngrok URL or deployed endpoint. (Project Requirements: Integration)
2.  In the `/app.py` file, integrate the logic so that upon receiving a `/leave` command, the modal defined in `/templates/leave_modal.json` is correctly opened for the user. (Project Requirements: Slash Command)
3.  Link the submit callback from the modal to post a message into the admin review Slack channel, ensuring all required fields are included. (Project Requirements: Admin Approval Workflow)
4.  Integrate the admin button responses to trigger either an immediate approval notification or to open a denial reason modal. (Project Requirements: Admin Approval Workflow)
5.  Craft the Slack notification messages to include appropriate instructions and confirmations for both the requester and the admin (clearly indicating that modifications/cancellations aren’t allowed and that a new request is required for changes). (Project Requirements: Notifications)
6.  **Validation**: Use Slack’s interactive message testing (or actual Slack test messages) to ensure that the entire flow—from invoking `/leave` to admin response and user notification—works end-to-end.

## Phase 5: Deployment

1.  Set up a Vultr server for hosting the Python backend. (Project Requirements: Deployment)
2.  Provision a Vultr instance ensuring it is configured for 24/7 availability and meets application resource needs. (Project Requirements: Deployment)
3.  Deploy the backend code to the Vultr server (e.g., using Git push or SCP to transfer code to the instance). (Project Requirements: Deployment)
4.  Install and configure a production-ready web server (e.g., Gunicorn) and set up a reverse proxy (e.g., Nginx) to serve the Python application. (Project Requirements: Deployment)
5.  Configure environment variables on the server (e.g., in a `.env` file or the server’s environment) for `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and any other required keys. (Project Requirements: Admin Approval Workflow)
6.  Update the Slack App configuration in the Slack dashboard with the Vultr instance’s public URL for slash commands and interactivity endpoints. (Project Requirements: Integration)
7.  Set Firewall and security rules on Vultr to accept only necessary traffic (e.g., from Slack IP ranges). (Project Requirements: Security/Error Handling)
8.  **Validation**: Perform end-to-end tests in the production environment by issuing the `/leave` command in Slack and following through all admin actions to verify functionality.

## Final Validation and Testing

1.  Perform user testing in a Slack testing workspace to ensure that the leave request modal displays correctly, accepts valid inputs, and that notifications are sent as designed. (Project Requirements: Modal Interface, Notifications)
2.  Validate that the admin approval workflow correctly distinguishes between admin users (via channel membership or configured Slack user IDs) and that denial reasons are collected when necessary. (Project Requirements: Admin Approval Workflow)
3.  Test error handling by providing invalid inputs and simulating connectivity issues to ensure informative error messages are displayed. (Project Requirements: Error Handling)
4.  Document all endpoints and main configuration settings in a README file for future developers. (Project Requirements: Documentation)
5.  Conduct a final review and testing session with a sample set of leave requests to validate system stability and correct Slack notifications. (Project Requirements: Final Verification)

-- Note: This implementation plan strictly follows the project requirements for the Slack-based leave request system, with a focus on utilizing Slack APIs, Block Kit for UI, and a Python backend deployed on Vultr. All configurations and interactions are designed to operate entirely within Slack to meet the project goal.
