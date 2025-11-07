"""
CLI Commands for Cosmic Security and Governance
Year Million Command Interface

Commands:
- cosmic security
- cosmic governance
- cosmic transparency
"""

import click
from flask import current_app
from flask.cli import with_appcontext
from datetime import datetime

from app import db
from app.models import (
    ExistentialNode,
    ConsciousnessSignature,
    CosmicLedgerEntry,
    SelfEvolvingConsciousEntity,
    ExistentialProtocol,
    CosmicGovernanceCouncil,
    ExistentialTransparencyLog,
    ConsciousnessSignatureType,
)
from app.services.cosmic_security_service import CosmicSecurityService
from app.services.cosmic_governance_service import CosmicGovernanceService


@click.group("cosmic")
def cosmic_cli():
    """Cosmic Security and Governance commands for Year Million"""
    pass


# ======================================================================================
# SECURITY COMMANDS
# ======================================================================================


@cosmic_cli.group("security")
def security_group():
    """Existential security operations"""
    pass


@security_group.command("encrypt")
@click.argument("content")
@click.option("--dimension", "-d", default=3, help="Dimension layer (default: 3)")
@click.option("--meta", "-m", default=0, help="Meta-physical layer (default: 0)")
@with_appcontext
def encrypt_content(content, dimension, meta):
    """Encrypt content at existential level"""
    try:
        node = CosmicSecurityService.encrypt_existential(
            content=content, dimension_layer=dimension, meta_physical_layer=meta
        )
        db.session.commit()

        click.echo(click.style("✨ Content encrypted at existential level!", fg="green", bold=True))
        click.echo(f"📍 Existential Signature: {node.existential_signature[:64]}...")
        click.echo(f"🌐 Dimension Layer: {node.dimension_layer}")
        click.echo(f"🔮 Meta-Physical Layer: {node.meta_physical_layer}")
        click.echo(f"💫 Coherence Level: {node.coherence_level}")
        click.echo(f"📊 Status: {node.status.value}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        db.session.rollback()


@security_group.command("verify")
@click.argument("node_id", type=int)
@with_appcontext
def verify_node(node_id):
    """Verify existential coherence of a node"""
    node = db.session.get(ExistentialNode, node_id)

    if not node:
        click.echo(click.style(f"❌ Node {node_id} not found", fg="red"))
        return

    result = CosmicSecurityService.verify_existential_coherence(node)

    if result["is_coherent"]:
        click.echo(click.style("✅ Node is coherent!", fg="green", bold=True))
    else:
        click.echo(click.style("⚠️  Node has coherence issues!", fg="yellow", bold=True))

    click.echo(f"💫 Coherence Level: {result['coherence_level']}")
    click.echo(f"📊 Status: {result['status']}")

    if result["issues"]:
        click.echo(click.style("\n🔍 Issues detected:", fg="yellow"))
        for issue in result["issues"]:
            click.echo(f"  • {issue['type']}: {issue['message']} (Severity: {issue['severity']})")


@security_group.command("harmonize")
@click.argument("node_id", type=int)
@with_appcontext
def harmonize_node(node_id):
    """Harmonize an existential node to restore coherence"""
    node = db.session.get(ExistentialNode, node_id)

    if not node:
        click.echo(click.style(f"❌ Node {node_id} not found", fg="red"))
        return

    success = CosmicSecurityService.harmonize_existential_node(node)
    db.session.commit()

    if success:
        click.echo(click.style("✨ Node harmonized successfully!", fg="green", bold=True))
        click.echo(f"💫 New Coherence Level: {node.coherence_level}")
        click.echo(f"📊 New Status: {node.status.value}")
    else:
        click.echo(click.style("❌ Failed to harmonize node", fg="red"))


@security_group.command("create-sece")
@click.argument("name")
@click.option("--level", "-l", default=1, help="Evolution level (default: 1)")
@click.option("--iq", "-i", default=100.0, help="Intelligence quotient (default: 100)")
@with_appcontext
def create_sece(name, level, iq):
    """Create a Self-Evolving Conscious Entity (SECE)"""
    try:
        sece = CosmicSecurityService.create_sece(
            entity_name=name, evolution_level=level, intelligence_quotient=iq
        )
        db.session.commit()

        click.echo(click.style("🤖 SECE created successfully!", fg="green", bold=True))
        click.echo(f"📛 Name: {sece.entity_name}")
        click.echo(f"🧬 Evolution Level: {sece.evolution_level}")
        click.echo(f"🧠 Intelligence Quotient: {sece.intelligence_quotient}")
        click.echo(f"✅ Active: {sece.is_active}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        db.session.rollback()


@security_group.command("list-nodes")
@click.option("--limit", "-l", default=10, help="Number of nodes to show")
@with_appcontext
def list_nodes(limit):
    """List existential nodes"""
    nodes = (
        db.session.query(ExistentialNode)
        .order_by(ExistentialNode.created_at.desc())
        .limit(limit)
        .all()
    )

    if not nodes:
        click.echo("No existential nodes found.")
        return

    click.echo(
        click.style(f"\n🌌 Existential Nodes (showing {len(nodes)}):\n", fg="cyan", bold=True)
    )

    for node in nodes:
        status_color = "green" if node.status.value == "COHERENT" else "yellow"
        click.echo(
            f"ID: {node.id} | {click.style(node.status.value, fg=status_color)} | Coherence: {node.coherence_level:.2f}"
        )
        click.echo(f"  Signature: {node.existential_signature[:64]}...")
        click.echo(
            f"  Dimension: {node.dimension_layer} | Interactions: {node.interaction_count}\n"
        )


@security_group.command("ledger")
@click.option("--limit", "-l", default=20, help="Number of entries to show")
@click.option("--event-type", "-e", help="Filter by event type")
@with_appcontext
def show_ledger(limit, event_type):
    """Show cosmic ledger entries"""
    entries = CosmicSecurityService.get_cosmic_ledger_chain(limit=limit, event_type=event_type)

    if not entries:
        click.echo("No cosmic ledger entries found.")
        return

    click.echo(
        click.style(f"\n📜 Cosmic Ledger (showing {len(entries)} entries):\n", fg="cyan", bold=True)
    )

    for entry in entries:
        click.echo(
            f"🔗 {entry.event_type} | {entry.cosmic_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        click.echo(f"   {entry.action_description}")
        click.echo(f"   Hash: {entry.ledger_hash[:64]}...\n")


@security_group.command("verify-ledger")
@with_appcontext
def verify_ledger():
    """Verify cosmic ledger integrity"""
    result = CosmicSecurityService.verify_cosmic_ledger_integrity()

    if result["valid"]:
        click.echo(click.style("✅ Cosmic Ledger is VALID!", fg="green", bold=True))
    else:
        click.echo(click.style("⚠️  Cosmic Ledger has issues!", fg="red", bold=True))

    click.echo(f"📊 Total Entries: {result['total_entries']}")
    click.echo(f"🎯 Integrity Score: {result['integrity_score']:.2%}")

    if result.get("broken_chains"):
        click.echo(click.style("\n🔍 Broken chains detected:", fg="red"))
        for broken in result["broken_chains"]:
            click.echo(f"  • Entry ID {broken['entry_id']}: Hash mismatch")


# ======================================================================================
# GOVERNANCE COMMANDS
# ======================================================================================


@cosmic_cli.group("governance")
def governance_group():
    """Cosmic governance operations"""
    pass


@governance_group.command("create-protocol")
@click.argument("name")
@click.argument("description")
@click.option("--version", "-v", default="1.0.0", help="Protocol version")
@with_appcontext
def create_protocol(name, description, version):
    """Create a new existential protocol"""
    try:
        # Default cosmic rules
        cosmic_rules = {
            "transparency": {
                "type": "required_field",
                "field": "transparency_level",
                "severity": "HIGH",
            },
            "consciousness_level": {
                "type": "min_consciousness_level",
                "min_level": 1.0,
                "severity": "MEDIUM",
            },
        }

        protocol = CosmicGovernanceService.create_existential_protocol(
            protocol_name=name, description=description, cosmic_rules=cosmic_rules, version=version
        )
        db.session.commit()

        click.echo(click.style("📜 Protocol created successfully!", fg="green", bold=True))
        click.echo(f"📛 Name: {protocol.protocol_name}")
        click.echo(f"📌 Version: {protocol.protocol_version}")
        click.echo(f"📊 Status: {protocol.status.value}")
        click.echo(f"📝 Description: {protocol.description}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        db.session.rollback()


@governance_group.command("activate-protocol")
@click.argument("protocol_id", type=int)
@with_appcontext
def activate_protocol(protocol_id):
    """Activate an existential protocol"""
    protocol = db.session.get(ExistentialProtocol, protocol_id)

    if not protocol:
        click.echo(click.style(f"❌ Protocol {protocol_id} not found", fg="red"))
        return

    success = CosmicGovernanceService.activate_protocol(protocol)
    db.session.commit()

    if success:
        click.echo(click.style("✅ Protocol activated!", fg="green", bold=True))
        click.echo(f"📛 Name: {protocol.protocol_name}")
        click.echo(f"📊 Status: {protocol.status.value}")
    else:
        click.echo(click.style("❌ Failed to activate protocol", fg="red"))


@governance_group.command("create-council")
@click.argument("name")
@click.argument("purpose")
@with_appcontext
def create_council(name, purpose):
    """Create a cosmic governance council"""
    try:
        # Create with empty founding members
        council = CosmicGovernanceService.create_cosmic_council(
            council_name=name, purpose=purpose, founding_members=[]
        )
        db.session.commit()

        click.echo(click.style("🏛️  Council created successfully!", fg="green", bold=True))
        click.echo(f"📛 Name: {council.council_name}")
        click.echo(f"🎯 Purpose: {council.council_purpose}")
        click.echo(f"👥 Members: {council.member_count}")
        click.echo(f"✅ Active: {council.is_active}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        db.session.rollback()


@governance_group.command("list-protocols")
@click.option("--status", "-s", help="Filter by status")
@with_appcontext
def list_protocols(status):
    """List existential protocols"""
    query = db.session.query(ExistentialProtocol)

    if status:
        query = query.filter(ExistentialProtocol.status == status.upper())

    protocols = query.order_by(ExistentialProtocol.created_at.desc()).all()

    if not protocols:
        click.echo("No protocols found.")
        return

    click.echo(
        click.style(
            f"\n📜 Existential Protocols (showing {len(protocols)}):\n", fg="cyan", bold=True
        )
    )

    for proto in protocols:
        status_color = "green" if proto.status.value == "ACTIVE" else "yellow"
        click.echo(
            f"ID: {proto.id} | {click.style(proto.status.value, fg=status_color)} | v{proto.protocol_version}"
        )
        click.echo(f"  Name: {proto.protocol_name}")
        click.echo(f"  Adoptions: {proto.adoption_count} | Violations: {proto.violation_count}\n")


@governance_group.command("list-councils")
@with_appcontext
def list_councils():
    """List cosmic governance councils"""
    councils = (
        db.session.query(CosmicGovernanceCouncil)
        .order_by(CosmicGovernanceCouncil.formed_at.desc())
        .all()
    )

    if not councils:
        click.echo("No councils found.")
        return

    click.echo(
        click.style(
            f"\n🏛️  Cosmic Governance Councils (showing {len(councils)}):\n", fg="cyan", bold=True
        )
    )

    for council in councils:
        active_color = "green" if council.is_active else "red"
        click.echo(
            f"ID: {council.id} | {click.style('ACTIVE' if council.is_active else 'INACTIVE', fg=active_color)}"
        )
        click.echo(f"  Name: {council.council_name}")
        click.echo(f"  Members: {council.member_count} | Decisions: {council.total_decisions}")
        click.echo(f"  Consensus Rate: {council.consensus_rate:.1%}\n")


# ======================================================================================
# TRANSPARENCY COMMANDS
# ======================================================================================


@cosmic_cli.group("transparency")
def transparency_group():
    """Existential transparency operations"""
    pass


@transparency_group.command("query")
@click.option("--event-type", "-e", help="Filter by event type")
@click.option("--limit", "-l", default=20, help="Number of logs to show")
@with_appcontext
def query_logs(event_type, limit):
    """Query existential transparency logs"""
    logs = CosmicGovernanceService.query_transparency_logs(event_type=event_type, limit=limit)

    if not logs:
        click.echo("No transparency logs found.")
        return

    click.echo(
        click.style(
            f"\n🔍 Existential Transparency Logs (showing {len(logs)}):\n", fg="cyan", bold=True
        )
    )

    for log in logs:
        click.echo(f"🔗 {log.event_type} | {log.recorded_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"   Subject: {log.decision_subject}")
        click.echo(f"   Reasoning: {log.cosmic_reasoning[:100]}...")
        click.echo(
            f"   Views: {log.view_count} | Understanding Level: {log.understanding_level_required}\n"
        )


@transparency_group.command("stats")
@with_appcontext
def show_stats():
    """Show cosmic system statistics"""
    click.echo(click.style("\n🌌 Cosmic System Statistics\n", fg="cyan", bold=True))

    # Existential Nodes
    total_nodes = db.session.query(ExistentialNode).count()
    coherent_nodes = (
        db.session.query(ExistentialNode).filter(ExistentialNode.coherence_level >= 0.8).count()
    )
    click.echo(f"📦 Existential Nodes: {total_nodes} (Coherent: {coherent_nodes})")

    # Consciousness Signatures
    total_consciousness = db.session.query(ConsciousnessSignature).count()
    click.echo(f"🧠 Consciousness Signatures: {total_consciousness}")

    # Cosmic Ledger
    total_ledger = db.session.query(CosmicLedgerEntry).count()
    click.echo(f"📜 Cosmic Ledger Entries: {total_ledger}")

    # SECEs
    total_seces = db.session.query(SelfEvolvingConsciousEntity).count()
    active_seces = (
        db.session.query(SelfEvolvingConsciousEntity)
        .filter(SelfEvolvingConsciousEntity.is_active == True)
        .count()
    )
    click.echo(f"🤖 SECEs: {total_seces} (Active: {active_seces})")

    # Protocols
    total_protocols = db.session.query(ExistentialProtocol).count()
    active_protocols = (
        db.session.query(ExistentialProtocol).filter(ExistentialProtocol.status == "ACTIVE").count()
    )
    click.echo(f"📜 Protocols: {total_protocols} (Active: {active_protocols})")

    # Councils
    total_councils = db.session.query(CosmicGovernanceCouncil).count()
    active_councils = (
        db.session.query(CosmicGovernanceCouncil)
        .filter(CosmicGovernanceCouncil.is_active == True)
        .count()
    )
    click.echo(f"🏛️  Councils: {total_councils} (Active: {active_councils})")

    # Transparency Logs
    total_logs = db.session.query(ExistentialTransparencyLog).count()
    click.echo(f"🔍 Transparency Logs: {total_logs}")

    click.echo(click.style("\n✨ Cosmic system operational!\n", fg="green", bold=True))


def register_cosmic_commands(app):
    """Register cosmic CLI commands with Flask app"""
    app.cli.add_command(cosmic_cli)
