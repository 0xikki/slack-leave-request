# Implementation plan

## Phase 1: Environment Setup ✅

1. ✅ Create a new project directory (e.g., `slack-leave-system`) and initialize a Git repository with `main` and `dev` branches. (Project Requirements: Overview)
2. ✅ Install the required Python version (use the default system Python, as no explicit version is given) and set up a virtual environment. (Project Requirements: Tech Stack - Backend)
3. ✅ Create a configuration file at `/config/config.json` to store Slack tokens, signing secret, admin Slack user IDs, and admin channel ID. (Project Requirements: Admin Approval Workflow)
4. ✅ Set environment variables for `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and any other secrets. (Project Requirements: Admin Approval Workflow)
5. ✅ Register a new Slack App via the Slack API dashboard and configure the slash command `/leave` with the request URL pointing to your development endpoint (e.g., using ngrok for local testing). (Project Requirements: Slash Command, Frontend/Integration)
6. ✅ **Validation**: Verify the Slack App settings in the dashboard to ensure the slash command configuration is correct.

## Phase 2: Slack UI (Frontend/Integration) Development ✅

1. ✅ Create a file `/templates/leave_modal.json` to define the Block Kit modal UI. (Project Requirements: Modal Interface)

2. ✅ In `/templates/leave_modal.json`, define fields for:

    *   Date(s) of absence (provide single date picker and/or a date range picker if supported)
    *   Reason for leave (plain text input)
    *   Type of leave (static select with options: Sick, Emergency, PTO, Holiday, Offset)
    *   Tasks to be covered (plain text input)
    *   Person who will cover (plain text input)
    *   Supporting document upload (this field can be represented as an optional attachment note if file upload isn't directly supported)
    *   A note indicating the times displayed are based on UK work hours (9 AM to 5 PM). (Project Requirements: Modal Interface)

3. ✅ Style the modal using Slack's Aubergine theme options if available. (Project Requirements: Modal Interface)

4. ✅ **Validation**: Use Slack's Block Kit Builder to preview and verify the layout and functionality of the modal.

## Phase 3: Backend Development ✅

1. ✅ Create the main backend application file `/app.py` using Flask to handle incoming Slack POST events. (Project Requirements: Backend)

2. ✅ In `/app.py`, set up an endpoint (e.g., `/slack/commands`) to receive slash command payloads from Slack. (Project Requirements: Slash Command)

3. ✅ Implement verification of Slack request signatures in the endpoint to ensure secure communication. (Project Requirements: Error Handling)

4. ✅ Within the `/slack/commands` endpoint, parse the `/leave` command payload and trigger the opening of the leave modal using Slack's `views.open` API call along with the JSON from `/templates/leave_modal.json`. (Project Requirements: Slash Command, Modal Interface)

5. ✅ Create another endpoint at `/slack/interactivity` to handle modal submission callbacks. (Project Requirements: Modal Interface)

6. ✅ In `/slack/interactivity`, process the modal submission data by extracting the leave request details. (Project Requirements: Modal Interface)

7. ✅ After processing a leave request, post a message to a dedicated Slack channel (e.g., `/slack/admin_notify`) informing admins of the new leave request with Approve and Deny buttons using Block Kit actions. (Project Requirements: Admin Approval Workflow)

8. ✅ Create helper functions in `/slack/helpers.py` for constructing Slack messages and modals to keep the code organized. (Project Requirements: Slack API Integration)

9. ✅ Create the endpoint `/slack/actions` to handle admin interactions (button clicks) from the leave request notification message. (Project Requirements: Admin Approval Workflow)

10. ✅ In `/slack/actions`, branch logic for Approve and Deny actions:

    *   For Approve: Immediately notify the requester of approval.
    *   For Deny: Trigger a modal prompting the admin for a reason, then notify the requester with the denial and reason. (Project Requirements: Admin Approval Workflow)

11. ✅ **Validation**: Test the endpoints locally by simulating slash command payloads and Slack interactivity payloads to ensure correct behavior.

## Phase 4: Integration ✅

1. ✅ Connect the backend endpoints with the Slack App configuration by updating the Request URL for slash commands and interactivity in the Slack dashboard to point to your ngrok URL or deployed endpoint. (Project Requirements: Integration)
2. ✅ In the `/app.py` file, integrate the logic so that upon receiving a `/leave` command, the modal defined in `/templates/leave_modal.json` is correctly opened for the user. (Project Requirements: Slash Command)
3. ✅ Link the submit callback from the modal to post a message into the admin review Slack channel, ensuring all required fields are included. (Project Requirements: Admin Approval Workflow)
4. ✅ Integrate the admin button responses to trigger either an immediate approval notification or to open a denial reason modal. (Project Requirements: Admin Approval Workflow)
5. ✅ Craft the Slack notification messages to include appropriate instructions and confirmations for both the requester and the admin. (Project Requirements: Notifications)
6. ✅ **Validation**: Use Slack's interactive message testing to ensure that the entire flow works end-to-end.

## Phase 5: Deployment ⏳ [NEXT]

1. ✅ Set up deployment configuration files:
   * Created `requirements.txt` with production dependencies
   * Created `gunicorn.conf.py` for production server
   * Created `nginx.conf` for reverse proxy
   * Created `slack-leave-system.service` for systemd service
   * Created `deploy.ps1` PowerShell deployment script

2. ⏳ Provision a Vultr instance ensuring it is configured for 24/7 availability:
   * Choose appropriate instance size (2 CPU, 4GB RAM recommended)
   * Select Ubuntu 22.04 LTS as the operating system
   * Configure networking and SSH access

3. 📝 Deploy the backend code to the Vultr server:
   * Run the deployment script with server details
   * Verify all services are running
   * Configure environment variables

4. 📝 Post-deployment tasks:
   * Update the Slack App configuration with the new domain
   * Verify SSL certificate installation
   * Test all endpoints through the production URL

5. 📝 Monitor and validate:
   * Set up logging and monitoring
   * Perform end-to-end testing in production
   * Document any production-specific configurations

## Final Validation and Testing (In Progress)

1. 📝 Perform user testing in a Slack testing workspace.
2. 📝 Validate the admin approval workflow.
3. ✅ Test error handling by providing invalid inputs.
4. ✅ Document all endpoints and main configuration settings in a README file.
5. 📝 Conduct a final review and testing session.

Legend:
- ✅ Completed
- ⏳ In Progress
- 📝 Not Started

-- Note: This implementation plan strictly follows the project requirements for the Slack-based leave request system, with a focus on utilizing Slack APIs, Block Kit for UI, and a Python backend deployed on Vultr. All configurations and interactions are designed to operate entirely within Slack to meet the project goal.
