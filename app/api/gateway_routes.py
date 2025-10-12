# app/api/gateway_routes.py
# ======================================================================================
# ==        API GATEWAY ROUTES - SUPERHUMAN ORCHESTRATION LAYER                     ==
# ======================================================================================
# PRIME DIRECTIVE:
#   طبقة تنسيق خارقة للتوجيه الذكي والتحميل المتوازن
#   Superhuman orchestration layer for intelligent routing and load balancing

from flask import request, jsonify, current_app
from app.api import api_bp
from app.services.api_gateway_service import get_gateway_service
from app.services.api_security_service import rate_limit
from app.services.api_observability_service import monitor_performance

# ======================================================================================
# GATEWAY CONTROL ENDPOINTS
# ======================================================================================

@api_bp.route('/gateway/health', methods=['GET'])
def gateway_health():
    """Check API Gateway health status"""
    try:
        gateway = get_gateway_service()
        health_status = gateway.get_health_status()
        
        return jsonify({
            'status': 'success',
            'data': health_status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Gateway health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Gateway health check failed'
        }), 503


@api_bp.route('/gateway/routes', methods=['GET'])
@rate_limit
def get_routes():
    """Get all registered gateway routes"""
    try:
        gateway = get_gateway_service()
        routes = gateway.get_all_routes()
        
        return jsonify({
            'status': 'success',
            'data': {
                'routes': routes,
                'count': len(routes)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting routes: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve routes'
        }), 500


@api_bp.route('/gateway/services', methods=['GET'])
@rate_limit
def get_services():
    """Get all upstream services"""
    try:
        gateway = get_gateway_service()
        services = gateway.get_all_services()
        
        return jsonify({
            'status': 'success',
            'data': {
                'services': services,
                'count': len(services)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting services: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve services'
        }), 500


@api_bp.route('/gateway/cache/stats', methods=['GET'])
@rate_limit
@monitor_performance
def get_cache_stats():
    """Get cache statistics"""
    try:
        gateway = get_gateway_service()
        stats = gateway.get_cache_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve cache statistics'
        }), 500


@api_bp.route('/gateway/cache/clear', methods=['POST'])
@rate_limit
def clear_cache():
    """Clear API Gateway cache"""
    try:
        gateway = get_gateway_service()
        gateway.clear_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to clear cache'
        }), 500


# ======================================================================================
# LOAD BALANCING & ROUTING
# ======================================================================================

@api_bp.route('/gateway/balancer/status', methods=['GET'])
@rate_limit
def get_balancer_status():
    """Get load balancer status"""
    try:
        gateway = get_gateway_service()
        status = gateway.get_balancer_status()
        
        return jsonify({
            'status': 'success',
            'data': status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting balancer status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve balancer status'
        }), 500


@api_bp.route('/gateway/routing/strategy', methods=['GET', 'PUT'])
@rate_limit
def routing_strategy():
    """Get or update routing strategy"""
    try:
        gateway = get_gateway_service()
        
        if request.method == 'GET':
            strategy = gateway.get_routing_strategy()
            return jsonify({
                'status': 'success',
                'data': {'strategy': strategy}
            }), 200
        
        else:  # PUT
            data = request.get_json()
            new_strategy = data.get('strategy')
            gateway.set_routing_strategy(new_strategy)
            
            return jsonify({
                'status': 'success',
                'message': f'Routing strategy updated to {new_strategy}'
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Error with routing strategy: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to manage routing strategy'
        }), 500


# ======================================================================================
# FEATURE FLAGS & A/B TESTING
# ======================================================================================

@api_bp.route('/gateway/features', methods=['GET'])
@rate_limit
def get_feature_flags():
    """Get all feature flags"""
    try:
        gateway = get_gateway_service()
        flags = gateway.get_feature_flags()
        
        return jsonify({
            'status': 'success',
            'data': {'flags': flags}
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting feature flags: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve feature flags'
        }), 500


@api_bp.route('/gateway/features/<feature_name>', methods=['PUT'])
@rate_limit
def toggle_feature(feature_name):
    """Toggle a feature flag"""
    try:
        gateway = get_gateway_service()
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        gateway.set_feature_flag(feature_name, enabled)
        
        return jsonify({
            'status': 'success',
            'message': f'Feature {feature_name} {"enabled" if enabled else "disabled"}'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error toggling feature {feature_name}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to toggle feature'
        }), 500


@api_bp.route('/gateway/experiments', methods=['GET'])
@rate_limit
def get_experiments():
    """Get all A/B test experiments"""
    try:
        gateway = get_gateway_service()
        experiments = gateway.get_experiments()
        
        return jsonify({
            'status': 'success',
            'data': {'experiments': experiments}
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting experiments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve experiments'
        }), 500


# ======================================================================================
# CHAOS ENGINEERING
# ======================================================================================

@api_bp.route('/gateway/chaos/experiments', methods=['GET'])
@rate_limit
def get_chaos_experiments():
    """Get active chaos engineering experiments"""
    try:
        from app.services.api_gateway_chaos import get_chaos_service
        chaos = get_chaos_service()
        experiments = chaos.get_active_experiments()
        
        return jsonify({
            'status': 'success',
            'data': {
                'active_experiments': experiments,
                'count': len(experiments)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting chaos experiments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve chaos experiments'
        }), 500


@api_bp.route('/gateway/chaos/inject', methods=['POST'])
@rate_limit
def inject_chaos():
    """Inject a chaos experiment"""
    try:
        from app.services.api_gateway_chaos import get_chaos_service
        chaos = get_chaos_service()
        data = request.get_json()
        
        experiment_id = chaos.inject_fault(
            fault_type=data.get('fault_type'),
            target_service=data.get('target_service'),
            fault_rate=data.get('fault_rate', 0.1)
        )
        
        return jsonify({
            'status': 'success',
            'data': {'experiment_id': experiment_id},
            'message': 'Chaos experiment started'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error injecting chaos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to inject chaos'
        }), 500


# ======================================================================================
# CIRCUIT BREAKER
# ======================================================================================

@api_bp.route('/gateway/circuit-breaker/status', methods=['GET'])
@rate_limit
def get_circuit_breaker_status():
    """Get circuit breaker status for all services"""
    try:
        gateway = get_gateway_service()
        status = gateway.get_circuit_breaker_status()
        
        return jsonify({
            'status': 'success',
            'data': status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting circuit breaker status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve circuit breaker status'
        }), 500


@api_bp.route('/gateway/circuit-breaker/<service_name>/reset', methods=['POST'])
@rate_limit
def reset_circuit_breaker(service_name):
    """Manually reset a circuit breaker"""
    try:
        gateway = get_gateway_service()
        gateway.reset_circuit_breaker(service_name)
        
        return jsonify({
            'status': 'success',
            'message': f'Circuit breaker for {service_name} reset successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error resetting circuit breaker: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to reset circuit breaker'
        }), 500
