# Verification Steps

This document outlines the manual verification steps required to ensure the application is running correctly in a GitHub Codespaces environment.

## 1. Making Port 8000 Public

After the application server starts, GitHub Codespaces will automatically forward port 8000. However, by default, it might be private. To make it accessible to everyone, follow these steps:

1.  **Open the Ports Tab**: In the bottom panel of your Codespaces window, click on the "Ports" tab.
2.  **Find Port 8000**: Locate the entry for port 8000 in the list.
3.  **Change Visibility**: Right-click on the port entry or click on the globe icon. Change the "Port Visibility" from "Private" to "**Public**".
4.  **Access the Application**: Use the "Local Address" URL provided in the same panel to access the running application. It should look something like `https://<your-codespace-name>-8000.app.github.dev/`.

By following these steps, the frontend of the CogniForge platform will be publicly accessible.
