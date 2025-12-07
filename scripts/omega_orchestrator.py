#!/usr/bin/env python3
"""
Ω OMEGA ORCHESTRATOR
====================
"The Central Nervous System of Intelligent DevOps"

This script unifies the disparate intelligence modules (Security, Sync, DevOps)
into a single, autonomous decision-making engine. It operates based on the
principles of the "Digital Singularity" report.

Capabilities:
- Context-Aware Execution (Local vs CI)
- Dynamic Module Loading
- Autonomous Self-Healing Triggering
- Unified Logging & Reporting
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime

# Import Sub-Systems
# Ensure scripts/ is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from scripts.security_gate import NeuralStaticAnalyzer, CodeAnomaly
    from scripts.universal_repo_sync import sync_remotes, check_workload_identity
    from app.services.agentic_devops import agentic_devops, DiagnosticResult
except ImportError as e:
    print(f"CRITICAL: Failed to load Omega Modules: {e}")
    sys.exit(1)

# Configure High-Order Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | Ω-CORE | %(levelname)s | %(message)s")
logger = logging.getLogger("OmegaOrchestrator")

class OmegaCore:
    def __init__(self, mode="monitor"):
        self.mode = mode
        self.security_engine = NeuralStaticAnalyzer()
        self.start_time = datetime.now()

    def analyze_environment(self):
        """
        Performs a deep scan of the execution environment.
        """
        env_context = {
            "ci_system": "GitHub Actions" if os.environ.get("GITHUB_ACTIONS") else
                         ("GitLab CI" if os.environ.get("GITLAB_CI") else "Local"),
            "workload_identity": check_workload_identity(),
            "python_version": sys.version.split()[0],
            "mode": self.mode
        }
        logger.info(f"Environment Analysis: {json.dumps(env_context, indent=2)}")
        return env_context

    def execute_security_protocol(self, target_path="."):
        """
        Runs the Security Gate and triggers Self-Healing if needed.
        """
        logger.info("🛡️ Initiating Omega Security Protocol...")
        anomalies = self.security_engine.scan_directory(target_path)

        criticals = [a for a in anomalies if a.severity == "CRITICAL"]
        highs = [a for a in anomalies if a.severity == "HIGH"]

        if not anomalies:
            logger.info("✅ Security Protocol Passed: Zero Anomalies.")
            return True

        logger.warning(f"⚠️ Detected {len(anomalies)} anomalies ({len(criticals)} Critical, {len(highs)} High).")

        # Self-Healing Logic
        if self.mode == "autonomous" and anomalies:
            self.engage_self_healing(anomalies)

        # Decision Gate
        if criticals:
            logger.error("⛔ Security Gate Lockdown: Critical threats present.")
            return False

        return True

    def engage_self_healing(self, anomalies):
        """
        Activates Agentic DevOps to repair code.
        """
        logger.info("🚑 Engaging Autonomous Repair Systems...")
        for anomaly in anomalies:
            logger.info(f"Analyzing anomaly in {anomaly.file_path}...")

            # Ask Agentic DevOps for a fix
            fix_content = agentic_devops.propose_fix(anomaly.file_path, anomaly.description)

            if fix_content:
                logger.info(f"💡 Fix generated for {anomaly.file_path}. Applying...")
                success = agentic_devops.apply_fix(anomaly.file_path, fix_content)
                if success:
                    logger.info("✅ Repair Successful.")
                else:
                    logger.error("❌ Repair Failed.")
            else:
                logger.info("ℹ️ No autonomous fix available. Human intervention required.")

    def run_sync_protocol(self):
        """
        Wraps the Universal Repo Sync.
        """
        logger.info("🔄 Initiating Universal Sync Protocol...")
        try:
            sync_remotes()
        except Exception as e:
            logger.error(f"Sync Protocol Failure: {e}")
            # In a real Omega system, we might retry or failover here.
            sys.exit(1)

    def run(self):
        logger.info("🚀 Omega Orchestrator Activated.")
        env = self.analyze_environment()

        # 1. Security First
        security_passed = self.execute_security_protocol()

        if not security_passed:
            logger.error("System Halted due to Security Violations.")
            sys.exit(1)

        # 2. Sync if in Deployment/Sync mode
        if self.mode == "sync":
            self.run_sync_protocol()

        logger.info("🏁 Omega Protocol Completed Successfully.")

def main():
    parser = argparse.ArgumentParser(description="Omega Orchestrator - Autonomous DevOps Engine")
    parser.add_argument("--mode", choices=["monitor", "autonomous", "sync", "diagnose"], default="monitor",
                        help="Operating Mode")
    args = parser.parse_args()

    core = OmegaCore(mode=args.mode)
    core.run()

if __name__ == "__main__":
    main()
