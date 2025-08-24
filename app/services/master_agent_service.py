# app/services/master_agent_service.py
# ======================================================================================
# ==                      THE GENESIS ORCHESTRATOR (Overmind v0.2.0)                  ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This service is the foundational implementation of the Overmind. It is no longer
#   a mock stub. It now interacts with the real database to create and manage the
#   initial state of a Mission.
#
#   This version lays the groundwork for the full planning and execution lifecycle.
#
# ARCHITECTURAL EVOLUTION:
#   - Moves from a mock dictionary response to creating a real, persistent `Mission` object.
#   - Correctly integrates with the Akashic Genome (`app/models.py`).
#   - Provides a stable, database-aware foundation for the `admin` UI and future services.

from __future__ import annotations
from flask import current_app
from app import db

# --- [THE NEW REALITY] ---
# We now import the real, persistent entities we will be creating.
from app.models import User, Mission, MissionStatus, log_mission_event, MissionEventType

__version__ = "0.2.0"

def start_mission(objective: str, initiator: User) -> Mission:
    """
    Initiates a new strategic mission by creating a real record in the database.
    This function is the sole entry point for creating new missions.
    
    Args:
        objective: The high-level goal provided by the architect.
        initiator: The authenticated User object who is starting the mission.
        
    Returns:
        The newly created and persisted Mission object.
        
    Raises:
        Exception: Propagates any database errors upwards to be handled by the API layer.
    """
    current_app.logger.info(
        f"[Overmind] Initiating new mission for User ID {initiator.id}. Objective: '{objective}'"
    )
    
    try:
        # 1. Create the Mission entity.
        #    The Akashic Genome (models.py) handles default values like status and timestamps.
        mission = Mission(
            objective=objective,
            initiator_id=initiator.id
            # status defaults to PENDING
        )
        
        # 2. Add to the session to prepare for persistence.
        db.session.add(mission)
        
        # 3. Log the creation event BEFORE the final commit.
        #    This ensures that if the commit fails, we don't have a dangling event.
        #    The event will be committed atomically with the mission itself.
        log_mission_event(
            mission=mission,
            event_type=MissionEventType.CREATED,
            payload={"objective": objective},
            note=f"Mission created by {initiator.email}."
        )
        
        # 4. Commit to the database. This is the atomic transaction that makes it real.
        #    Upon commit, SQLAlchemy will assign a real `mission.id`.
        db.session.commit()
        
        current_app.logger.info(f"Successfully created Mission #{mission.id} in the Akashic Records.")
        
        # 5. Return the REAL, persisted Mission object.
        #    This object now has a `.id` attribute that the route handler can use.
        return mission

    except Exception as e:
        # If anything goes wrong, roll back the entire transaction to leave the
        # database in a clean state.
        db.session.rollback()
        current_app.logger.error(f"Catastrophic failure during mission creation: {e}", exc_info=True)
        # Re-raise the exception to let the calling layer (the API route) know
        # that a failure occurred so it can return a 500 error.
        raise