# Domain Model & System Boundaries

This document defines the high-level architecture of Cogniforge, dividing the system into distinct **Domains** (Areas of Responsibility) and **Layers** (Technical concerns).

## 1. Domain Map

The system is divided into four primary domains. Each domain represents a distinct business capability.

| Domain | Description | Key Responsibilities |
| :--- | :--- | :--- |
| **1. Identity & Access (IAM)** | User Management & Security | • Authentication (Login/Register)<br>• Authorization (RBAC, Policies)<br>• Session Management (JWT)<br>• User Profiles |
| **2. Cogniforge Core (Reality)** | Core Business Logic | • Project Management<br>• File Operations (Analysis/Transformation)<br>• Chat History & Persistence<br>• Subscription/Billing Logic |
| **3. Overmind Intelligence** | AI Orchestration | • LLM Gateway (Neural Routing Mesh)<br>• Agent Orchestration<br>• Planning & Reasoning (Deep Indexing)<br>• Tool Execution |
| **4. Infrastructure (Platform)** | Technical Foundation | • Database Access (SQLAlchemy)<br>• Configuration (Settings)<br>• Observability (Logging/Metrics)<br>• External Integrations (Git, Cloud) |

---

## 2. Layered Architecture (Per Domain)

Within each Domain, we enforce a strict 4-layer architecture to ensure Separation of Concerns (SoC).

### Layer 1: API (Interface)
*   **Purpose:** Handle external interaction (HTTP, CLI, WebSocket).
*   **Components:** FastAPI Routers, Pydantic Request/Response Schemas, CLI Handlers.
*   **Rule:** logic here should be limited to parsing input and formatting output. No business rules.

### Layer 2: Application (Use Cases)
*   **Purpose:** Orchestrate business flows.
*   **Components:** Services, Orchestrators, Use Case classes.
*   **Rule:** Coordinates the *Domain* and *Infrastructure* to achieve a user goal. Does not know about HTTP.

### Layer 3: Domain (Core)
*   **Purpose:** Pure business logic and state definition.
*   **Components:** Entities (Models), Value Objects, Domain Services/Rules.
*   **Rule:** Pure Python. No dependencies on frameworks (FastAPI) or Infrastructure (DB drivers).

### Layer 4: Infrastructure (Implementation)
*   **Purpose:** Implement interfaces defined by inner layers.
*   **Components:** Repositories (SQL), AI Clients (OpenAI/Anthropic), File System Adapters.
*   **Rule:** The only layer allowed to touch "dirty" external systems (IO).

---

## 3. Visual Reference

```mermaid
graph TD
    subgraph "Identity Domain"
        ID_API[API Layer] --> ID_APP[Application Layer]
        ID_APP --> ID_DOM[Domain Layer]
        ID_INFRA[Infrastructure Layer] -.->|Implements| ID_APP
    end

    subgraph "Overmind Domain"
        AI_API[API Layer] --> AI_APP[Application Layer]
        AI_APP --> AI_DOM[Domain Layer]
        AI_INFRA[Infrastructure Layer] -.->|Implements| AI_APP
    end

    %% Cross-Domain Dependencies
    ID_APP -.->|Uses| AI_APP
```
