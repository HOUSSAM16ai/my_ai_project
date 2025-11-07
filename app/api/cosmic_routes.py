"""
Cosmic Security and Governance API Routes
Year Million REST API

Endpoints:
- /api/cosmic/security/*
- /api/cosmic/governance/*
- /api/cosmic/transparency/*
"""

from flask import Blueprint, request, jsonify
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

cosmic_bp = Blueprint('cosmic', __name__, url_prefix='/api/cosmic')


# ======================================================================================
# SECURITY ENDPOINTS
# ======================================================================================

@cosmic_bp.route('/security/encrypt', methods=['POST'])
def encrypt_existential():
    """
    Encrypt content at existential level
    
    Body:
        content: str - Content to encrypt
        dimension_layer: int - Dimension layer (default: 3)
        meta_physical_layer: int - Meta-physical layer (default: 0)
        consciousness_id: int - Optional consciousness ID
    """
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                'ok': False,
                'error': 'Content is required'
            }), 400
        
        node = CosmicSecurityService.encrypt_existential(
            content=data['content'],
            consciousness_id=data.get('consciousness_id'),
            dimension_layer=data.get('dimension_layer', 3),
            meta_physical_layer=data.get('meta_physical_layer', 0)
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'data': {
                'node_id': node.id,
                'existential_signature': node.existential_signature,
                'cosmic_hash': node.cosmic_hash,
                'dimension_layer': node.dimension_layer,
                'meta_physical_layer': node.meta_physical_layer,
                'status': node.status.value,
                'coherence_level': node.coherence_level,
                'created_at': node.created_at.isoformat(),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@cosmic_bp.route('/security/nodes/<int:node_id>', methods=['GET'])
def get_existential_node(node_id):
    """Get existential node by ID"""
    node = db.session.get(ExistentialNode, node_id)
    
    if not node:
        return jsonify({
            'ok': False,
            'error': 'Node not found'
        }), 404
    
    return jsonify({
        'ok': True,
        'data': {
            'id': node.id,
            'existential_signature': node.existential_signature,
            'cosmic_hash': node.cosmic_hash,
            'dimension_layer': node.dimension_layer,
            'meta_physical_layer': node.meta_physical_layer,
            'status': node.status.value,
            'coherence_level': node.coherence_level,
            'distortion_count': node.distortion_count,
            'interaction_count': node.interaction_count,
            'created_at': node.created_at.isoformat(),
            'last_accessed_at': node.last_accessed_at.isoformat(),
            'last_harmonized_at': node.last_harmonized_at.isoformat(),
        }
    })


@cosmic_bp.route('/security/nodes/<int:node_id>/verify', methods=['POST'])
def verify_node_coherence(node_id):
    """Verify existential coherence of a node"""
    node = db.session.get(ExistentialNode, node_id)
    
    if not node:
        return jsonify({
            'ok': False,
            'error': 'Node not found'
        }), 404
    
    result = CosmicSecurityService.verify_existential_coherence(node)
    
    return jsonify({
        'ok': True,
        'data': result
    })


@cosmic_bp.route('/security/nodes/<int:node_id>/harmonize', methods=['POST'])
def harmonize_node(node_id):
    """Harmonize an existential node"""
    node = db.session.get(ExistentialNode, node_id)
    
    if not node:
        return jsonify({
            'ok': False,
            'error': 'Node not found'
        }), 404
    
    data = request.get_json() or {}
    consciousness_id = data.get('consciousness_id')
    
    success = CosmicSecurityService.harmonize_existential_node(node, consciousness_id)
    db.session.commit()
    
    if success:
        return jsonify({
            'ok': True,
            'data': {
                'node_id': node.id,
                'status': node.status.value,
                'coherence_level': node.coherence_level,
                'last_harmonized_at': node.last_harmonized_at.isoformat(),
            }
        })
    else:
        return jsonify({
            'ok': False,
            'error': 'Failed to harmonize node'
        }), 500


@cosmic_bp.route('/security/nodes', methods=['GET'])
def list_existential_nodes():
    """List existential nodes with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = db.session.query(ExistentialNode)
    
    if status:
        query = query.filter(ExistentialNode.status == status.upper())
    
    pagination = query.order_by(
        ExistentialNode.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    nodes = [{
        'id': node.id,
        'existential_signature': node.existential_signature[:64] + '...',
        'dimension_layer': node.dimension_layer,
        'status': node.status.value,
        'coherence_level': node.coherence_level,
        'interaction_count': node.interaction_count,
    } for node in pagination.items]
    
    return jsonify({
        'ok': True,
        'data': nodes,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })


@cosmic_bp.route('/security/consciousness', methods=['POST'])
def create_consciousness():
    """Create a consciousness signature"""
    try:
        data = request.get_json()
        
        if not data or 'entity_name' not in data or 'entity_type' not in data:
            return jsonify({
                'ok': False,
                'error': 'entity_name and entity_type are required'
            }), 400
        
        # Validate entity type
        try:
            entity_type = ConsciousnessSignatureType[data['entity_type'].upper()]
        except KeyError:
            return jsonify({
                'ok': False,
                'error': f"Invalid entity_type. Must be one of: {[t.name for t in ConsciousnessSignatureType]}"
            }), 400
        
        consciousness = CosmicSecurityService.create_consciousness_signature(
            entity_name=data['entity_name'],
            entity_type=entity_type,
            entity_origin=data.get('entity_origin'),
            consciousness_level=data.get('consciousness_level', 1.0)
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'data': {
                'id': consciousness.id,
                'signature_hash': consciousness.signature_hash,
                'entity_name': consciousness.entity_name,
                'entity_type': consciousness.entity_type.value,
                'consciousness_level': consciousness.consciousness_level,
                'first_seen_at': consciousness.first_seen_at.isoformat(),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@cosmic_bp.route('/security/sece', methods=['POST'])
def create_sece():
    """Create a Self-Evolving Conscious Entity"""
    try:
        data = request.get_json()
        
        if not data or 'entity_name' not in data:
            return jsonify({
                'ok': False,
                'error': 'entity_name is required'
            }), 400
        
        sece = CosmicSecurityService.create_sece(
            entity_name=data['entity_name'],
            evolution_level=data.get('evolution_level', 1),
            intelligence_quotient=data.get('intelligence_quotient', 100.0)
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'data': {
                'id': sece.id,
                'entity_name': sece.entity_name,
                'evolution_level': sece.evolution_level,
                'intelligence_quotient': sece.intelligence_quotient,
                'is_active': sece.is_active,
                'created_at': sece.created_at.isoformat(),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@cosmic_bp.route('/security/ledger', methods=['GET'])
def get_cosmic_ledger():
    """Get cosmic ledger entries"""
    limit = request.args.get('limit', 100, type=int)
    event_type = request.args.get('event_type')
    
    entries = CosmicSecurityService.get_cosmic_ledger_chain(
        limit=limit,
        event_type=event_type
    )
    
    ledger = [{
        'id': entry.id,
        'ledger_hash': entry.ledger_hash[:64] + '...',
        'event_type': entry.event_type,
        'action_description': entry.action_description,
        'cosmic_timestamp': entry.cosmic_timestamp.isoformat(),
        'dimension_layer': entry.dimension_layer,
    } for entry in entries]
    
    return jsonify({
        'ok': True,
        'data': ledger,
        'meta': {
            'total': len(ledger),
            'event_type_filter': event_type,
        }
    })


@cosmic_bp.route('/security/ledger/verify', methods=['GET'])
def verify_ledger_integrity():
    """Verify cosmic ledger integrity"""
    result = CosmicSecurityService.verify_cosmic_ledger_integrity()
    
    return jsonify({
        'ok': True,
        'data': result
    })


# ======================================================================================
# GOVERNANCE ENDPOINTS
# ======================================================================================

@cosmic_bp.route('/governance/protocols', methods=['POST'])
def create_protocol():
    """Create an existential protocol"""
    try:
        data = request.get_json()
        
        if not data or 'protocol_name' not in data or 'description' not in data:
            return jsonify({
                'ok': False,
                'error': 'protocol_name and description are required'
            }), 400
        
        protocol = CosmicGovernanceService.create_existential_protocol(
            protocol_name=data['protocol_name'],
            description=data['description'],
            cosmic_rules=data.get('cosmic_rules', {}),
            version=data.get('version', '1.0.0')
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'data': {
                'id': protocol.id,
                'protocol_name': protocol.protocol_name,
                'protocol_version': protocol.protocol_version,
                'description': protocol.description,
                'status': protocol.status.value,
                'created_at': protocol.created_at.isoformat(),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@cosmic_bp.route('/governance/protocols/<int:protocol_id>/activate', methods=['POST'])
def activate_protocol(protocol_id):
    """Activate an existential protocol"""
    protocol = db.session.get(ExistentialProtocol, protocol_id)
    
    if not protocol:
        return jsonify({
            'ok': False,
            'error': 'Protocol not found'
        }), 404
    
    success = CosmicGovernanceService.activate_protocol(protocol)
    db.session.commit()
    
    if success:
        return jsonify({
            'ok': True,
            'data': {
                'protocol_id': protocol.id,
                'protocol_name': protocol.protocol_name,
                'status': protocol.status.value,
                'activated_at': protocol.activated_at.isoformat() if protocol.activated_at else None,
            }
        })
    else:
        return jsonify({
            'ok': False,
            'error': 'Failed to activate protocol'
        }), 500


@cosmic_bp.route('/governance/protocols', methods=['GET'])
def list_protocols():
    """List existential protocols"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = db.session.query(ExistentialProtocol)
    
    if status:
        query = query.filter(ExistentialProtocol.status == status.upper())
    
    pagination = query.order_by(
        ExistentialProtocol.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    protocols = [{
        'id': proto.id,
        'protocol_name': proto.protocol_name,
        'protocol_version': proto.protocol_version,
        'status': proto.status.value,
        'adoption_count': proto.adoption_count,
        'violation_count': proto.violation_count,
    } for proto in pagination.items]
    
    return jsonify({
        'ok': True,
        'data': protocols,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })


@cosmic_bp.route('/governance/councils', methods=['POST'])
def create_council():
    """Create a cosmic governance council"""
    try:
        data = request.get_json()
        
        if not data or 'council_name' not in data or 'purpose' not in data:
            return jsonify({
                'ok': False,
                'error': 'council_name and purpose are required'
            }), 400
        
        council = CosmicGovernanceService.create_cosmic_council(
            council_name=data['council_name'],
            purpose=data['purpose'],
            founding_members=data.get('founding_members', [])
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'data': {
                'id': council.id,
                'council_name': council.council_name,
                'council_purpose': council.council_purpose,
                'member_count': council.member_count,
                'is_active': council.is_active,
                'formed_at': council.formed_at.isoformat(),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@cosmic_bp.route('/governance/councils', methods=['GET'])
def list_councils():
    """List cosmic governance councils"""
    councils = db.session.query(CosmicGovernanceCouncil).order_by(
        CosmicGovernanceCouncil.formed_at.desc()
    ).all()
    
    council_list = [{
        'id': council.id,
        'council_name': council.council_name,
        'member_count': council.member_count,
        'total_decisions': council.total_decisions,
        'consensus_rate': council.consensus_rate,
        'is_active': council.is_active,
    } for council in councils]
    
    return jsonify({
        'ok': True,
        'data': council_list,
        'meta': {
            'total': len(council_list),
        }
    })


@cosmic_bp.route('/governance/councils/<int:council_id>/analytics', methods=['GET'])
def get_council_analytics(council_id):
    """Get analytics for a cosmic council"""
    council = db.session.get(CosmicGovernanceCouncil, council_id)
    
    if not council:
        return jsonify({
            'ok': False,
            'error': 'Council not found'
        }), 404
    
    analytics = CosmicGovernanceService.get_council_analytics(council)
    
    return jsonify({
        'ok': True,
        'data': analytics
    })


# ======================================================================================
# TRANSPARENCY ENDPOINTS
# ======================================================================================

@cosmic_bp.route('/transparency/logs', methods=['GET'])
def query_transparency():
    """Query existential transparency logs"""
    event_type = request.args.get('event_type')
    limit = request.args.get('limit', 100, type=int)
    min_understanding = request.args.get('min_understanding_level', 0.0, type=float)
    
    logs = CosmicGovernanceService.query_transparency_logs(
        event_type=event_type,
        min_understanding_level=min_understanding,
        limit=limit
    )
    
    log_list = [{
        'id': log.id,
        'event_hash': log.event_hash[:64] + '...',
        'event_type': log.event_type,
        'decision_subject': log.decision_subject,
        'cosmic_reasoning': log.cosmic_reasoning[:200] + '...' if len(log.cosmic_reasoning) > 200 else log.cosmic_reasoning,
        'understanding_level_required': log.understanding_level_required,
        'view_count': log.view_count,
        'recorded_at': log.recorded_at.isoformat(),
    } for log in logs]
    
    return jsonify({
        'ok': True,
        'data': log_list,
        'meta': {
            'total': len(log_list),
            'event_type_filter': event_type,
        }
    })


@cosmic_bp.route('/transparency/logs/<int:log_id>', methods=['GET'])
def get_transparency_log(log_id):
    """Get detailed transparency log"""
    log = db.session.get(ExistentialTransparencyLog, log_id)
    
    if not log:
        return jsonify({
            'ok': False,
            'error': 'Transparency log not found'
        }), 404
    
    # Increment view count
    log.view_count += 1
    db.session.commit()
    
    return jsonify({
        'ok': True,
        'data': {
            'id': log.id,
            'event_hash': log.event_hash,
            'event_type': log.event_type,
            'decision_subject': log.decision_subject,
            'decision_details': log.decision_details,
            'underlying_motivations': log.underlying_motivations,
            'cosmic_reasoning': log.cosmic_reasoning,
            'cosmic_fabric_impact': log.cosmic_fabric_impact,
            'affected_dimensions': log.affected_dimensions,
            'understanding_level_required': log.understanding_level_required,
            'shared_consciousness_field': log.shared_consciousness_field,
            'view_count': log.view_count,
            'recorded_at': log.recorded_at.isoformat(),
        }
    })


@cosmic_bp.route('/stats', methods=['GET'])
def cosmic_stats():
    """Get cosmic system statistics"""
    stats = {
        'existential_nodes': {
            'total': db.session.query(ExistentialNode).count(),
            'coherent': db.session.query(ExistentialNode).filter(
                ExistentialNode.coherence_level >= 0.8
            ).count(),
        },
        'consciousness_signatures': {
            'total': db.session.query(ConsciousnessSignature).count(),
        },
        'cosmic_ledger': {
            'total_entries': db.session.query(CosmicLedgerEntry).count(),
        },
        'seces': {
            'total': db.session.query(SelfEvolvingConsciousEntity).count(),
            'active': db.session.query(SelfEvolvingConsciousEntity).filter(
                SelfEvolvingConsciousEntity.is_active == True
            ).count(),
        },
        'protocols': {
            'total': db.session.query(ExistentialProtocol).count(),
            'active': db.session.query(ExistentialProtocol).filter(
                ExistentialProtocol.status == 'ACTIVE'
            ).count(),
        },
        'councils': {
            'total': db.session.query(CosmicGovernanceCouncil).count(),
            'active': db.session.query(CosmicGovernanceCouncil).filter(
                CosmicGovernanceCouncil.is_active == True
            ).count(),
        },
        'transparency_logs': {
            'total': db.session.query(ExistentialTransparencyLog).count(),
        },
    }
    
    return jsonify({
        'ok': True,
        'data': stats,
        'meta': {
            'timestamp': datetime.now().isoformat(),
            'system': 'Cosmic Security and Governance - Year Million',
        }
    })


@cosmic_bp.route('/health', methods=['GET'])
def cosmic_health():
    """Cosmic system health check"""
    try:
        # Check database connectivity
        db.session.query(ExistentialNode).limit(1).all()
        
        # Verify ledger integrity
        ledger_integrity = CosmicSecurityService.verify_cosmic_ledger_integrity()
        
        return jsonify({
            'ok': True,
            'status': 'operational',
            'data': {
                'database_connected': True,
                'ledger_integrity': ledger_integrity['integrity_score'],
                'ledger_valid': ledger_integrity['valid'],
            },
            'meta': {
                'timestamp': datetime.now().isoformat(),
                'message': 'Cosmic fabric is stable',
            }
        })
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'status': 'degraded',
            'error': str(e)
        }), 503


def register_cosmic_routes(app):
    """Register cosmic routes with Flask app"""
    app.register_blueprint(cosmic_bp)
