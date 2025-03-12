# Tech Stack Document

## Introduction

This project is designed to create an intuitive time-off and leave request system that operates entirely within Slack. Users can simply type a slash command to open a modal, fill in details such as the dates of absence, leave type, reason, and more, while administrators review requests directly in a dedicated Slack channel. The system embraces Slack’s native visual style, using an aubergine theme when possible, and ensures that all time information reflects UK working hours. This document explains the rationale behind each technology choice and how they contribute to the overall system’s goals and user experience.

## Frontend Technologies

The user interface is built with Slack’s built-in tools, primarily utilizing the Slack API and Block Kit. When a user issues the slash command, a modal appears with form components allowing for date selection, reason entry, leave type selection, and even file uploads for supporting documents. These components not only ensure quick data entry within Slack’s ecosystem but also maintain consistency with the familiar look and feel of the Slack interface. The design has been carefully planned so that every interaction, from opening the modal to receiving notifications, feels natural and intuitive to the end user.

## Backend Technologies

On the backend, Python serves as the primary programming language to handle the logic and processing of leave requests. Python scripts are used to manage interactions between the modal input and the Slack API, directing submissions to the correct Slack channel where administrators can review them. Even though the current version does not incorporate a permanent data store, the backend is designed to process requests robustly and is structured to integrate with additional storage solutions or external systems in the future. The use of Python provides a flexible and scalable foundation capable of supporting future enhancements such as syncing with calendars or HR systems.

## Infrastructure and Deployment

The entire application is hosted on Vultr, which ensures reliable and continuous uptime without the need for local server management. Vultr’s infrastructure supports 24/7 availability, making sure that the Slack-integrated system is always ready to handle requests. Development and deployment workflows are streamlined to allow for rapid iterations and troubleshooting. While a traditional CI/CD pipeline may be implemented later as the system evolves, the current setup relies on proven practices to maintain code quality and deploy seamlessly from development to production environments.

## Third-Party Integrations

At the core of this project is the deep integration with Slack. Everything from the slash commands to the interactive modal experiences is driven by Slack’s API. Slack’s Block Kit is used to design the interface, ensuring that the modal not only complies with Slack’s visual guidelines but also meets user expectations in terms of ease of use and responsiveness. This tight integration leverages the existing Slack platform, reducing the need for additional web-based components and ensuring that users remain within their familiar workspace environment.

## Security and Performance Considerations

Security is maintained through Slack’s inherent authentication and user management, which restricts leave request submission and administration to verified workspace members only. Admin access is further confined by Slack channel membership and configuration settings that define authorized Slack IDs. On the performance front, the system is optimized for rapid response; the modal interface and notification mechanisms are designed to function within seconds of the slash command. Error states, such as invalid input or connectivity issues, are handled gracefully, ensuring that users receive clear feedback without disruption. These precautions help create a secure, fast, and reliable service that meets business requirements while reducing the risk of unauthorized access or data mishandling.

## Conclusion and Overall Tech Stack Summary

In summary, this project leverages Slack’s API and Block Kit to provide an integrated, user friendly leave request system, with Python powering the backend logic for managing requests and ensuring smooth interactions. Hosting on Vultr guarantees robust performance and uptime, while the exclusive use of Slack for user interactions simplifies the overall design and enhances security. Unique elements such as the aubergine-themed modal and direct Slack notifications ensure a cohesive and modern user experience. Each component of the tech stack has been chosen to align with the goals of rapid deployment, transparency in administration, and scalability for future integrations, setting this project apart as a streamlined solution for managing time-off requests within the familiar Slack environment.
