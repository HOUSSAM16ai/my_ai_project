# Verification and Manual Steps

This document provides instructions for verifying the application's status and performing necessary manual configurations in GitHub Codespaces.

## How to Make Port 8000 Public in GitHub Codespaces

To access the application from your browser, you must ensure that the forwarded port `8000` is set to "Public".

1.  **Open the Ports Tab:** In your GitHub Codespaces window, look for the "PORTS" tab. It is usually located in the terminal panel at the bottom of the screen. Click on it to view the list of forwarded ports.

2.  **Locate Port 8000:** Find the entry for port `8000` in the list.

3.  **Check Visibility:** Look at the "Visibility" column for that port. If it says "Private", you need to change it.

4.  **Change to Public:** Right-click on the port `8000` entry and select "Change Port Visibility" -> "Public".

5.  **Verify:** The visibility should now show "Public". You can now access the application by clicking the "Local Address" URL (the one that looks like `https://*.app.github.dev`).
