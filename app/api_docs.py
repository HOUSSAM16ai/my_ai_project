from typing import Any


def _get_health_docs() ->dict[str, Any]:
    return {'GET /api/health': {'summary': 'System health check',
        'description': 'Get system health status and metrics', 'tags': [
        'Health'], 'responses': {(200): {'description': 'System is healthy',
        'example': {'success': True, 'data': {'status': 'healthy',
        'database': 'connected', 'uptime': 3600}}}}}}


def _get_database_docs() ->dict[str, Any]:
    return {'GET /admin/api/database/tables': {'summary':
        'List all database tables', 'description':
        'Get list of all tables with metadata and statistics', 'tags': [
        'Database'], 'responses': {(200): {'description': 'List of tables',
        'example': {'status': 'success', 'tables': [{'name': 'users',
        'count': 42, 'icon': '👤', 'category': 'Core'}]}}}},
        'GET /admin/api/database/stats': {'summary': 'Database statistics',
        'description': 'Get comprehensive database statistics and metrics',
        'tags': ['Database']}, 'GET /admin/api/database/health': {'summary':
        'Database health check', 'description':
        'Check database connection and health status', 'tags': ['Database']}}


def _get_crud_docs() ->dict[str, Any]:
    return {'GET /admin/api/database/table/<table_name>': {'summary':
        'Get table data', 'description':
        'Retrieve paginated data from a specific table', 'tags': [
        'Database'], 'parameters': [{'name': 'table_name', 'in': 'path',
        'required': True, 'type': 'string', 'description':
        'Name of the table'}, {'name': 'page', 'in': 'query', 'type':
        'integer', 'default': 1, 'description': 'Page number'}, {'name':
        'per_page', 'in': 'query', 'type': 'integer', 'default': 50,
        'description': 'Items per page (max 100)'}, {'name': 'search', 'in':
        'query', 'type': 'string', 'description': 'Search query'}, {'name':
        'order_by', 'in': 'query', 'type': 'string', 'description':
        'Field to order by'}, {'name': 'order_dir', 'in': 'query', 'type':
        'string', 'enum': ['asc', 'desc'], 'default': 'asc', 'description':
        'Order direction'}]},
        'GET /admin/api/database/record/<table_name>/<id>': {'summary':
        'Get single record', 'description':
        'Retrieve a single record by ID', 'tags': ['Database']},
        'POST /admin/api/database/record/<table_name>': {'summary':
        'Create record', 'description':
        'Create a new record in the specified table', 'tags': ['Database']},
        'PUT /admin/api/database/record/<table_name>/<id>': {'summary':
        'Update record', 'description': 'Update an existing record', 'tags':
        ['Database']},
        'DELETE /admin/api/database/record/<table_name>/<id>': {'summary':
        'Delete record', 'description': 'Delete a record by ID', 'tags': [
        'Database']}}
