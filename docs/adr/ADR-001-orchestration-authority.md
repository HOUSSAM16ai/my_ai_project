# ADR-001: Orchestration Authority

## Status
Accepted

## Date
2026-02-10

## Decision
`orchestrator_service` (specifically the backend Overmind logic) is the **sole coordinator** of the system.

## Context
The system was suffering from complex state management issues where the frontend attempted to infer the state of the mission or agent execution. This led to "hysterical" reconnects, conflicting UI states (connected + disconnected), and brittle UX.

## Constraints
1. **No Orchestration Logic in Frontend**: The frontend must not attempt to guess the next step or manage the state of the mission. It is a "dumb" terminal that renders events.
2. **No Orchestration Logic in `app/services/chat`**: The chat service acts as a gateway/interface. It should not contain complex orchestration logic. It delegates to the `Overmind` or `orchestrator_service`.

## Implementation

### Frontend Authority
The frontend operates on a strict **Command -> Event** pattern:
- **Command**: User sends a message or action (e.g., "Start Mission").
- **Event**: The frontend listens for `agent:event` (via WebSocket).
- The frontend **never** predicts the next state. It only renders what the backend reports.

### Connection Management
- The WebSocket connection is purely a transport layer for events.
- UI state (e.g., input disabling) MUST NOT be coupled to the connection state in a blocking way.
- Reconnection logic uses exponential backoff and does not trigger UI "flashing".

### Backend Authority
- The `MissionComplexHandler` (or equivalent orchestrator) is the single source of truth.
- It emits specific events (`phase_start`, `phase_completed`, `loop_start`) that the frontend consumes directly.

## Consequences
- **Positive**:
    - "Brain" logic is centralized.
    - Frontend becomes significantly simpler and more robust.
    - Adding new agents or phases does not require frontend code changes (if using generic event rendering).
- **Negative**:
    - Network latency might cause a slight delay in state updates (acceptable for this use case).
