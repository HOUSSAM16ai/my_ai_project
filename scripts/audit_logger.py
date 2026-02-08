#!/usr/bin/env python3
"""
🛡️ JULES AUDIT LOGGER
=====================
Implements the "Observability & Audit" requirement.
Logs every action taken by the agent to a structured JSONL file.
"""

import argparse
import json
import logging
import os
from datetime import UTC, datetime

# Configure internal logging for the script itself
logging.basicConfig(level=logging.INFO, format="%(asctime)s | AUDIT | %(levelname)s | %(message)s")
logger = logging.getLogger("AuditLogger")


class JulesAuditLogger:
    def __init__(self, log_path: str = "logs/jules_audit.jsonl"):
        self.log_path = log_path
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        dirname = os.path.dirname(self.log_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

    def log_action(
        self,
        actor: str,
        action_type: str,
        target: str,
        reason: str,
        impact: str,
        status: str = "SUCCESS",
        metadata: dict[str, object] | None = None,
    ):
        """
        Logs a structured event to the audit file.
        """
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "action_type": action_type,
            "target": target,
            "reason": reason,
            "impact": impact,
            "status": status,
            "metadata": metadata or {},
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            logger.info(f"Logged action: {action_type} on {target}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


def main():
    parser = argparse.ArgumentParser(description="Log an action to the Jules Audit Trail")
    parser.add_argument("--actor", default="Jules-Agent", help="Who performed the action")
    parser.add_argument(
        "--action", required=True, help="What action was taken (e.g., CREATE_FILE, REFACTOR)"
    )
    parser.add_argument("--target", required=True, help="Target file or system")
    parser.add_argument("--reason", required=True, help="Why this action was taken")
    parser.add_argument("--impact", required=True, help="Expected impact of this action")
    parser.add_argument("--status", default="SUCCESS", help="Outcome status")

    args = parser.parse_args()

    audit = JulesAuditLogger()
    audit.log_action(
        actor=args.actor,
        action_type=args.action,
        target=args.target,
        reason=args.reason,
        impact=args.impact,
        status=args.status,
    )


if __name__ == "__main__":
    main()
