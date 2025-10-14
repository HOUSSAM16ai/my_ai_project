"""
Takbak API Routes - مسارات واجهة برمجة التطبيقات للطبقات
=========================================================
RESTful API endpoints for the Takbak (layers) management service.

الغرض (Purpose):
واجهة برمجية لإدارة الطبقات التنظيمية في المنصة التعليمية
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.takbak_service import TakbakService

# Create blueprint for takbak routes
takbak_bp = Blueprint('takbak', __name__, url_prefix='/api/v1/takbak')

# Initialize service (in production, this would use dependency injection)
takbak_service = TakbakService()


@takbak_bp.route('/layers', methods=['GET'])
@login_required
def list_layers():
    """
    List all layers or filter by parent

    Query Parameters:
        parent_id: Optional parent layer ID to filter by
        include_children: Whether to include children info (default: true)

    Returns:
        JSON response with layers list
    """
    try:
        parent_id = request.args.get('parent_id')
        include_children = request.args.get('include_children', 'true').lower() == 'true'

        layers = takbak_service.list_layers(
            parent_id=parent_id,
            include_children=include_children
        )

        return jsonify({
            'ok': True,
            'data': layers,
            'count': len(layers)
        }), 200

    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 400


@takbak_bp.route('/layers', methods=['POST'])
@login_required
def create_layer():
    """
    Create a new layer

    Request Body:
        {
            "layer_id": "unique-id",
            "name": "Layer Name",
            "description": "Optional description",
            "parent_id": "optional-parent-id",
            "metadata": {}
        }

    Returns:
        JSON response with created layer
    """
    try:
        data = request.get_json()

        if not data or 'layer_id' not in data or 'name' not in data:
            return jsonify({
                'ok': False,
                'error': 'layer_id and name are required'
            }), 400

        layer = takbak_service.create_layer(
            layer_id=data['layer_id'],
            name=data['name'],
            description=data.get('description', ''),
            parent_id=data.get('parent_id'),
            metadata=data.get('metadata')
        )

        return jsonify({
            'ok': True,
            'data': layer,
            'message': 'Layer created successfully'
        }), 201

    except ValueError as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/layers/<layer_id>', methods=['GET'])
@login_required
def get_layer(layer_id):
    """
    Get a specific layer by ID

    Args:
        layer_id: The layer identifier

    Returns:
        JSON response with layer data
    """
    try:
        layer = takbak_service.get_layer(layer_id)

        if not layer:
            return jsonify({
                'ok': False,
                'error': f'Layer {layer_id} not found'
            }), 404

        return jsonify({
            'ok': True,
            'data': layer
        }), 200

    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/layers/<layer_id>', methods=['PUT'])
@login_required
def update_layer(layer_id):
    """
    Update an existing layer

    Args:
        layer_id: The layer to update

    Request Body:
        {
            "name": "New name",
            "description": "New description",
            "metadata": {}
        }

    Returns:
        JSON response with updated layer
    """
    try:
        data = request.get_json()

        layer = takbak_service.update_layer(
            layer_id=layer_id,
            name=data.get('name'),
            description=data.get('description'),
            metadata=data.get('metadata')
        )

        return jsonify({
            'ok': True,
            'data': layer,
            'message': 'Layer updated successfully'
        }), 200

    except ValueError as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/layers/<layer_id>', methods=['DELETE'])
@login_required
def delete_layer(layer_id):
    """
    Delete a layer

    Args:
        layer_id: The layer to delete

    Query Parameters:
        cascade: If true, delete all children recursively (default: false)

    Returns:
        JSON response confirming deletion
    """
    try:
        cascade = request.args.get('cascade', 'false').lower() == 'true'

        success = takbak_service.delete_layer(layer_id, cascade=cascade)

        if not success:
            return jsonify({
                'ok': False,
                'error': f'Layer {layer_id} not found'
            }), 404

        return jsonify({
            'ok': True,
            'message': f'Layer {layer_id} deleted successfully'
        }), 200

    except ValueError as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/hierarchy', methods=['GET'])
@login_required
def get_hierarchy():
    """
    Get the complete hierarchy tree

    Query Parameters:
        root_id: Optional root layer ID. If not provided, returns all roots

    Returns:
        JSON response with hierarchical tree
    """
    try:
        root_id = request.args.get('root_id')

        hierarchy = takbak_service.get_hierarchy(root_id)

        return jsonify({
            'ok': True,
            'data': hierarchy
        }), 200

    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/layers/<layer_id>/path', methods=['GET'])
@login_required
def get_layer_path(layer_id):
    """
    Get the path from root to the specified layer

    Args:
        layer_id: The target layer

    Returns:
        JSON response with path array
    """
    try:
        path = takbak_service.get_path(layer_id)

        if not path:
            return jsonify({
                'ok': False,
                'error': f'Layer {layer_id} not found'
            }), 404

        return jsonify({
            'ok': True,
            'data': path,
            'depth': len(path)
        }), 200

    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@takbak_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        JSON response with service status
    """
    return jsonify({
        'ok': True,
        'service': 'takbak',
        'status': 'healthy',
        'version': '1.0.0'
    }), 200
