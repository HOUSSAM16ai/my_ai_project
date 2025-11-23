# 🚀 COGNIFORGE SUPERHUMAN ACCESS GUIDE

## 🌟 Overview

Welcome to the **CogniForge Reality Kernel V3**. This system has been purified and enhanced to meet "Superhuman" standards of engineering, featuring a clean separation of concerns, advanced security, and a unified "Energy Engine" for AI interactions.

---

## 🔗 Step-by-Step: From CodeSpaces to Superhuman Admin

Follow this exact protocol to access the system from a fresh GitHub CodeSpace.

### Phase 1: Connection (Supabase)

The system requires a connection to your Supabase database to persist the "Superhuman" data structures.

1.  **Open CodeSpace**: Wait for the container to build and the terminal to be ready.
2.  **Set Environment Secrets**:
    You need to tell the system where your Supabase database is.

    *   **Get your Connection String**:
        1. Go to your [Supabase Dashboard](https://supabase.com/dashboard/project/aocnuqhxrhxgbfcgbxfy).
        2. Navigate to **Project Settings** -> **Database**.
        3. Copy the **Connection String** (use the Transaction Pooler or Session mode, e.g., `postgres://postgres.[project]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`).

    *   **Export in Terminal**:
        Run this command in the CodeSpace terminal (replace with your actual URL and password):
        ```bash
        export DATABASE_URL="postgresql://postgres.your-project:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        export SECRET_KEY="super-secret-key-change-this"
        export OPENROUTER_API_KEY="your-ai-key-here" # Required for Chat
        ```

### Phase 2: Genesis (Database Setup)

Once the variables are set, you must initialize the "Reality Kernel" schema.

1.  **Run Migrations**:
    This creates the tables (`users`, `admin_conversations`, `admin_messages`) in Supabase.
    ```bash
    alembic upgrade head
    ```

2.  **Seed the Admin User**:
    This creates the Superhuman Admin account.
    ```bash
    export ADMIN_EMAIL="admin@cogniforge.com"
    export ADMIN_PASSWORD="admin123"
    python scripts/seed_admin.py
    ```
    *Result*: You should see `✅ Admin user admin@cogniforge.com created successfully.`

### Phase 3: Launch

1.  **Start the Reality Kernel**:
    ```bash
    scripts/start.sh
    ```
    *Note*: If `scripts/start.sh` is not found or fails, run:
    ```bash
    uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
    ```

2.  **Access the Interface**:
    -   Click the **PORTS** tab in VS Code / CodeSpaces.
    -   Find **Port 8000**.
    -   Click the **Globe Icon** (Open in Browser).

### Phase 4: The Experience

1.  **Login Screen**:
    -   You will see the new "Superhuman" login interface.
    -   Enter Email: `admin@cogniforge.com`
    -   Enter Password: `admin123`

2.  **Admin Dashboard**:
    -   You are now in the **Neural Interface**.
    -   **Chat**: Type a message to the AI. It will stream back a response.
    -   **History**: Because you are connected to Supabase, **all previous messages are loaded**. The system fetches the last 20 messages from the `admin_messages` table every time you open a conversation.

---

## 💎 Superhuman Database Architecture

The data layer (`app/models.py`) is engineered for absolute consistency and performance.

-   **Unified Schema**: Uses `SQLModel` to bridge the gap between Python objects and Relational Tables.
-   **Adaptive Types**: Features a custom `JSONText` type decorator that automatically adapts between PostgreSQL `JSONB` (Production) and SQLite `TEXT` (Testing).
-   **Strict Integrity**: Enforced via rigorous Foreign Keys (`ForeignKey`) and Database Indexes (`index=True`) on critical fields.
-   **Audit Trails**: Every entity tracks `created_at` and `updated_at` timestamps with server-side defaults.

---
*System Status: ABSOLUTE GREEN*
