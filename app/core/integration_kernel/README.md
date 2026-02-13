# Integration Micro-Kernel Architecture

This directory contains the core components of the Integration Micro-Kernel, which replaces the monolithic `MCPIntegrations` class.

## Components

### 1. Canonical IR (`ir.py`)
Defines the Intermediate Representations (Data Transfer Objects) for all integration requests.
- `WorkflowPlan`: For agent workflows (LangGraph).
- `RetrievalQuery`: For semantic search (LlamaIndex).
- `PromptProgram`: For prompt optimization (DSPy).
- `ScoringSpec`: For re-ranking (CrossEncoders).
- `AgentAction`: For tool execution (Kagent).

### 2. Contracts (`contracts.py`)
Defines the abstract base classes (Interfaces) that all Drivers must implement.
- `WorkflowEngine`
- `RetrievalEngine`
- `PromptEngine`
- `RankingEngine`
- `ActionEngine`

### 3. Runtime (`runtime.py`)
The `IntegrationKernel` singleton that orchestrates requests. It uses the `PolicyManager` to route IR objects to the appropriate Driver.

### 4. Policy (`policy.py`)
Manages the registration and retrieval of Drivers. It allows for swapping implementations (e.g., switching from LocalGateway to a Remote API) via configuration.

## Usage

```python
from app.core.integration_kernel import IntegrationKernel, RetrievalQuery

kernel = IntegrationKernel()
query = RetrievalQuery(query="Solar panels", top_k=5)
result = await kernel.search(query, engine="llamaindex")
```
