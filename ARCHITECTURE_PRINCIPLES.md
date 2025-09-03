# ARCHITECTURE_PRINCIPLES.md

## Introduction

CogniForge is a modern AI-powered web application built with a microservice architecture. The system consists of a Flask-based web frontend, a FastAPI AI service, and a PostgreSQL database. This document outlines the architectural principles, components, data flows, and design considerations that govern the system's implementation.

The architecture follows a layered approach with clear separation of concerns, containerized deployment, and environment-specific configurations. The system is designed to handle AI model integration with a focus on maintainability, security, and scalability.

## Layered Overview

CogniForge implements a multi-layered architecture:

1. **Infrastructure Layer**
   - Docker containerization with multi-stage builds
   - Docker Compose orchestration
   - Custom bridge network ("appnet") for service communication

2. **Data Layer**
   - PostgreSQL database (Supabase)
   - SQLAlchemy ORM
   - Flask-Migrate for schema migrations

3. **Application Layer**
   - Flask web framework
   - Flask-Login for authentication
   - Flask-WTF for form handling and CSRF protection

4. **AI/ML Layer**
   - FastAPI service for AI operations
   - OpenAI API integration (default: GPT-4o)
   - Sentence Transformers for embeddings
   - Overmind Planners for AI planning

5. **Configuration Layer**
   - Environment-based configuration system
   - Dotenv for environment variable management
   - Hierarchical configuration classes

## Components & Services

### Web Service (Flask Frontend)
- Serves the web interface and handles user interactions
- Manages authentication and session state
- Processes form submissions
- Communicates with the AI service
- Implements database operations via SQLAlchemy

### AI Service (FastAPI)
- Runs as a separate microservice
- Handles AI model loading and inference
- Exposes API endpoints for AI operations
- Isolates resource-intensive AI processing

### Database Service
- PostgreSQL for persistent data storage
- Provides health checks for dependency management
- Maintains data integrity

### Application Factory
- Creates and configures the Flask application
- Registers extensions, blueprints, and routes
- Sets up logging and initializes AI planners
- Provides context management for CLI operations

### CLI Interface
- Enhanced command-line interface using Typer and Rich
- Provides administrative and operational capabilities

## Data Flow & Persistence

### Data Flow Patterns
- **Web → AI Service**: HTTP-based communication for AI processing
- **Web → Database**: Direct database access via SQLAlchemy ORM
- **CLI → Services**: Command-line interface for administrative operations

### Persistence Mechanisms
- **Primary Database**: PostgreSQL via Supabase
- **ORM Layer**: SQLAlchemy with connection pooling
- **Environment-Specific Configurations**:
  - Development: Local Dockerized PostgreSQL
  - Testing: In-memory SQLite
  - Production: Persistent PostgreSQL

### Database Resilience
- Connection pooling with pre-ping for reliability
- Health checks ensure database readiness before service startup

## Internal & External Dependencies

### Key External Dependencies
- **Web Framework**: Flask, Werkzeug, Gunicorn
- **AI/ML Stack**: PyTorch (CPU), Transformers, Sentence-Transformers, OpenAI
- **Database**: PostgreSQL, psycopg2-binary
- **Asynchronous Services**: FastAPI, Uvicorn