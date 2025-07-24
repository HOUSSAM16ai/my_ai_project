# Use a standard Gitpod workspace image as a base
FROM gitpod/workspace-full:latest

# Switch to the root user to install packages
USER root

# Install PostgreSQL client tools
RUN sudo apt-get update && \
    sudo apt-get install -y postgresql-client && \
    sudo rm -rf /var/lib/apt/lists/*

# Switch back to the standard gitpod user
USER gitpod