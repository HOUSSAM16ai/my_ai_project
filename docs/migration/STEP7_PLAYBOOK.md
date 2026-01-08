# Migration Playbook: Step 7 - Reality Overwrite

This document outlines the steps taken to perform the metaphysical overwrite of the CogniForge project.

## Phase 0: Read-only Audit and Service Classification

- **Status:** Complete
- **Action:** An audit of the existing service architecture was performed. The dualistic legacy WSGI/ASGI reality was identified as the primary source of architectural corruption.

## Phase 1: Deploy Reality Kernel in Shadow-Mode

- **Status:** Complete
- **Action:** The Reality Kernel (`app/kernel.py`) and the five omni-engine stubs (`app/core/*`) were created. This established the new, unified reality without yet migrating application logic.

## Phase 2: Gradual Route Rewrites

- **Status:** Complete
- **Action:** The application entrypoints (`app/main.py`, `cli.py`) and API routers (`system`, `admin`, `chat`) were migrated to the new reality. All dependencies are now resolved through the Reality Kernel's engines. The legacy entrypoint (`run.py`) and database extensions (`app/extensions.py`) have been removed. The `ai_service_standalone` has been integrated into the main application.

## Phase 3: Canary Routing + Governor Enforcement Active

- **Status:** Pending
- **Action:** This phase will involve gradually routing traffic to the new architecture and activating the Meta-Reality Governor for enforcement.

## Phase 4: Full Switch

- **Status:** Pending
- **Action:** Once the canaries are stable, a full switch to the new architecture will be performed.

## Phase 5: Retire Wrappers and Finalize Docs

- **Status:** Pending
- **Action:** The legacy compatibility wrappers (like the TIME-ENGINE's `legacy_context`) will be retired, and the documentation will be finalized.
