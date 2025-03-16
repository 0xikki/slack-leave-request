# Updated Project Requirements Document (PRD)

## 1. Project Overview

This project aims to develop a time-off/leave request system that operates entirely within Slack, thereby eliminating the need for a separate web interface. It streamlines the leave management process for users and administrators, featuring a Slack-based workflow for submitting and processing requests. Users can trigger a leave request modal by typing the slash command `/leave`, which prompts them to fill in essential leave details like dates, type, reason, and coverage plans. The system focuses on enhancing productivity by integrating with Slack, an already familiar platform for many users.

The system's objectives include facilitating quick user interactions, transparent notification processes for both submissions and approvals, and secure management by allowing only designated admins to oversee approvals and denials within Slack. Future scalability is anticipated, with potential plans to integrate this system with external HR or calendar software. Deployment will ensure 24/7 uptime via Vultr, providing robust and continuous service availability.

## 2. In-Scope vs. Out-of-Scope

**In-Scope:**

*   Slack-based interaction through the slash command `/timeoff`.

*   A modal UI for data input, including:

    *   Date picker for single date entry or date range selection.
    *   Text entry for the leave reason.
    *   Dropdown menu for leave types (Sick, Emergency, PTO, Holiday, Offset).
    *   Text fields for task coverage details and specifying a substitute cover person.
    *   An option to upload supporting documents.
    *   A display note indicating UK working hours (9 am to 5 pm) in the modal for clarity.

*   Requests directed to a designated Slack channel for administrator review.

*   Notifications to users upon leave approval or denial (including reason via modal for denials).

*   Admin identification based on Slack channel membership or pre-configured Slack IDs.

**Out-of-Scope:**

*   A separate web-based admin interface.
*   Modifications or cancellations of submitted leave requests via the system; resubmission of a new request is required for changes.
*   Integration with external systems such as HR or calendar tools—considered for future iterations.
*   Communication outside Slack (e.g., email alerts) for notifications.

## 3. User Flow

### User Initiation

*   **Step 1:** User types `/timeoff` in Slack to open the leave request modal.
*   **Step 2:** User enters leave details: the date(s) of absence, reason for the leave, type of leave, tasks for coverage, and the covering colleague, including uploading any relevant documents.
*   **Step 3:** User submits their request, automatically redirecting it to a specific Slack channel for admin review.

### Admin Review & Notification

*   **Step 4:** Admins review requests within the Slack channel, leveraging their channel membership or configured Slack ID for access.

    *   **Approvals:** Trigger a Slack notification to the user confirming the request approval.
    *   **Denials:** Open a secondary modal to specify a denial reason, that is then sent to the user in a Slack notification.

This Slack-only workflow maintains a structured, easy-to-follow process bolstered by clear, contextual notifications.

## 4. Core Features

*   **Slack Integration:**

    *   Leveraging slash command (`/timeoff`) to engage with Slack’s API.
    *   Maintain all interactions within Slack's environment for user ease.

*   **Dynamic Modal Interface:**

    *   Form fields for date selection (single or range).
    *   Input for leave reason and dropdown for leave type options.
    *   Sections for outlining task coverage and assigned responsibilities.
    *   Document upload feature within the modal.
    *   UI designed in the aubergine Slack theme when possible.

*   **Approval Workflow within Slack:**

    *   Direct request routing to a Slack channel for admin decisions.
    *   Approval-triggered notifications inform users promptly.
    *   Denial prompts a modal for reason entry, directly notified to users.

*   **Configurable Admin Access:**

    *   Admins designated via Slack channel membership or pre-set IDs.

## 5. Tech Stack & Tools

*   **Frontend and Integration:**

    *   Slack API for command execution, modal interfaces, and notifications.
    *   Block Kit for designing user interfaces with preference for the aubergine theme.

*   **Backend Processing:**

    *   Utilizing Python for managing Slack interactions and request logic.
    *   Initial version without a persistent data store, focusing on manual request management.

*   **Deployment and Continuous Operation:**

    *   Hosted on Vultr for 24/7 availability, ensuring consistent uptime.

*   **IDE/Development Tools:**

    *   Cursor to assist with AI-driven code generation and editing.

## 6. Non-Functional Requirements

*   **Performance:**

    *   Modal triggers and notifications must occur within seconds.
    *   System should handle Slack rate limits gracefully, ensuring reliability.

*   **Security and Compliance:**

    *   Enforced admin access through Slack membership or ID configuration.
    *   All Slack to backend communications (if integrated) to use encrypted channels.
    *   Maintain data privacy in line with company standards, even if manually managed initially.

*   **Usability and Design Adherence:**

    *   UI aligns with Slack's design ethos for usability.
    *   Notifications and guidance are clear, minimizing user error.

## 7. Constraints & Assumptions

*   The system operates exclusively within Slack, utilizing its API and modal capabilities.
*   Adherence to Slack’s UI customization options is presumed, with the aubergine theme being conditionally supported.
*   Admin capabilities depend on static Slack channel membership or a configuration file for user IDs.
*   At launch, the absence of a formal backend for data persistence is deliberate, with manual management prioritized.
*   Future expansion into integrations is assumed but not yet realized in this version.

## 8. Known Issues & Potential Pitfalls

*   API rate limitations may affect the speed and reliability of modal and notification functions.
*   Limited theming options in Slack could necessitate fallback to default theme aesthetics.
*   The absence of backend storage may complicate leave tracking, necessitating a manual tracking solution until feature expansion.
*   Admin governance is tightly linked to Slack channels, with potential risks if channels are mismanaged.
*   Attachment capabilities in Slack may have constraints related to file size or format, for which user guidelines will be necessary.

This PRD provides a comprehensive outline for a Slack-integrated leave request system, emphasizing user-friendly operation within existing workplace tools, facilitating swift and seamless deployment via Vultr, and offering a structure for iterative growth based on the needs of users and admins alike.
