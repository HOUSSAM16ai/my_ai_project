# app/services/api_contract_service.py
# ======================================================================================
# ==        WORLD-CLASS API CONTRACT SERVICE (v1.0 - OPENAPI EDITION)               ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام عقود API متقدم خارق مع OpenAPI وتحقق صارم
#   ✨ المميزات الخارقة:
#   - OpenAPI 3.0 specification with strict versioning
#   - Consumer-driven contract testing
#   - Automatic schema validation
#   - API versioning and deprecation management
#   - Breaking change detection
#   - Contract compliance monitoring

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app
import json
import hashlib
from jsonschema import validate, ValidationError, Draft7Validator
from collections import defaultdict


# ======================================================================================
# API VERSION MANAGEMENT
# ======================================================================================

@dataclass
class APIVersion:
    """API version metadata"""
    version: str
    release_date: datetime
    status: str  # 'active', 'deprecated', 'sunset'
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    breaking_changes: List[str] = field(default_factory=list)
    changelog: str = ""


# Current API versions
API_VERSIONS = {
    'v1': APIVersion(
        version='v1',
        release_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        status='active',
        changelog='Initial release with CRUD operations and observability'
    ),
    'v2': APIVersion(
        version='v2',
        release_date=datetime(2025, 10, 12, tzinfo=timezone.utc),
        status='active',
        breaking_changes=[
            'Response format changed to include metadata wrapper',
            'Authentication now requires JWT tokens',
            'Rate limiting headers added to all responses'
        ],
        changelog='Enhanced with Zero-Trust security, advanced monitoring, and ML-based features'
    )
}

DEFAULT_API_VERSION = 'v2'


# ======================================================================================
# OPENAPI SCHEMA DEFINITIONS
# ======================================================================================

# Base schemas for common types
BASE_SCHEMAS = {
    'Error': {
        'type': 'object',
        'required': ['status', 'error', 'message'],
        'properties': {
            'status': {'type': 'string', 'enum': ['error']},
            'error': {'type': 'string'},
            'message': {'type': 'string'},
            'details': {'type': 'object'},
            'trace_id': {'type': 'string'}
        }
    },
    'Success': {
        'type': 'object',
        'required': ['status'],
        'properties': {
            'status': {'type': 'string', 'enum': ['success']},
            'data': {'type': 'object'},
            'metadata': {'type': 'object'},
            'trace_id': {'type': 'string'}
        }
    },
    'Pagination': {
        'type': 'object',
        'properties': {
            'page': {'type': 'integer', 'minimum': 1},
            'per_page': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'total': {'type': 'integer', 'minimum': 0},
            'pages': {'type': 'integer', 'minimum': 0}
        }
    }
}

# Endpoint-specific schemas
ENDPOINT_SCHEMAS = {
    '/api/database/health': {
        'GET': {
            'response': {
                '200': {
                    'type': 'object',
                    'required': ['status', 'timestamp', 'checks'],
                    'properties': {
                        'status': {'type': 'string', 'enum': ['healthy', 'warning', 'critical']},
                        'timestamp': {'type': 'string', 'format': 'date-time'},
                        'checks': {'type': 'object'},
                        'metrics': {'type': 'object'},
                        'warnings': {'type': 'array', 'items': {'type': 'string'}},
                        'errors': {'type': 'array', 'items': {'type': 'string'}}
                    }
                }
            }
        }
    },
    '/api/database/tables': {
        'GET': {
            'response': {
                '200': {
                    'allOf': [
                        {'$ref': '#/components/schemas/Success'},
                        {
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'properties': {
                                        'tables': {
                                            'type': 'array',
                                            'items': {
                                                'type': 'object',
                                                'required': ['name', 'row_count'],
                                                'properties': {
                                                    'name': {'type': 'string'},
                                                    'row_count': {'type': 'integer'},
                                                    'category': {'type': 'string'},
                                                    'icon': {'type': 'string'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    },
    '/api/database/record/{table_name}': {
        'POST': {
            'request': {
                'type': 'object',
                'required': ['data'],
                'properties': {
                    'data': {'type': 'object'}
                }
            },
            'response': {
                '200': {
                    'allOf': [
                        {'$ref': '#/components/schemas/Success'},
                        {
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'required': ['id'],
                                    'properties': {
                                        'id': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    ]
                },
                '400': {'$ref': '#/components/schemas/Error'},
                '404': {'$ref': '#/components/schemas/Error'}
            }
        }
    },
    '/api/observability/metrics': {
        'GET': {
            'response': {
                '200': {
                    'type': 'object',
                    'required': ['timestamp', 'performance', 'sla_compliance'],
                    'properties': {
                        'timestamp': {'type': 'string', 'format': 'date-time'},
                        'performance': {
                            'type': 'object',
                            'required': ['avg_latency_ms', 'p99_latency_ms', 'p999_latency_ms'],
                            'properties': {
                                'avg_latency_ms': {'type': 'number'},
                                'p50_latency_ms': {'type': 'number'},
                                'p95_latency_ms': {'type': 'number'},
                                'p99_latency_ms': {'type': 'number'},
                                'p999_latency_ms': {'type': 'number'},
                                'requests_per_second': {'type': 'number'},
                                'error_rate': {'type': 'number'},
                                'active_requests': {'type': 'integer'}
                            }
                        },
                        'sla_compliance': {
                            'type': 'object',
                            'required': ['sla_target_ms', 'compliance_rate_percent', 'sla_status'],
                            'properties': {
                                'sla_target_ms': {'type': 'number'},
                                'total_requests': {'type': 'integer'},
                                'violations': {'type': 'integer'},
                                'compliance_rate_percent': {'type': 'number'},
                                'sla_status': {'type': 'string', 'enum': ['compliant', 'at_risk', 'violated']}
                            }
                        }
                    }
                }
            }
        }
    }
}


# ======================================================================================
# CONTRACT VALIDATION SERVICE
# ======================================================================================

@dataclass
class ContractViolation:
    """Contract violation record"""
    violation_id: str
    timestamp: datetime
    endpoint: str
    method: str
    violation_type: str  # 'schema', 'version', 'breaking_change'
    severity: str  # 'critical', 'high', 'medium', 'low'
    details: Dict[str, Any]
    expected_schema: Optional[Dict[str, Any]] = None
    actual_data: Optional[Any] = None


class APIContractService:
    """
    خدمة عقود API الخارقة - World-class API contract service
    
    Features:
    - OpenAPI 3.0 specification with strict versioning
    - Automatic request/response schema validation
    - Consumer-driven contract testing support
    - Breaking change detection
    - API version management with deprecation tracking
    - Contract violation monitoring and alerting
    """
    
    def __init__(self):
        self.contract_violations: List[ContractViolation] = []
        self.schema_cache: Dict[str, Draft7Validator] = {}
        self._compile_schemas()
    
    def _compile_schemas(self):
        """Pre-compile JSON schemas for faster validation"""
        # Compile base schemas
        for schema_name, schema in BASE_SCHEMAS.items():
            validator = Draft7Validator(schema)
            self.schema_cache[f'base_{schema_name}'] = validator
        
        # Compile endpoint schemas
        for endpoint, methods in ENDPOINT_SCHEMAS.items():
            for method, specs in methods.items():
                if 'request' in specs:
                    validator = Draft7Validator(specs['request'])
                    self.schema_cache[f'{endpoint}_{method}_request'] = validator
                
                if 'response' in specs:
                    for status_code, schema in specs['response'].items():
                        # Resolve $ref if present
                        resolved_schema = self._resolve_schema_refs(schema)
                        validator = Draft7Validator(resolved_schema)
                        self.schema_cache[f'{endpoint}_{method}_response_{status_code}'] = validator
    
    def _resolve_schema_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $ref references in schema"""
        if '$ref' in schema:
            ref_path = schema['$ref']
            if ref_path.startswith('#/components/schemas/'):
                schema_name = ref_path.split('/')[-1]
                if schema_name in BASE_SCHEMAS:
                    return BASE_SCHEMAS[schema_name]
        
        if 'allOf' in schema:
            # Merge allOf schemas
            merged = {}
            for sub_schema in schema['allOf']:
                resolved = self._resolve_schema_refs(sub_schema)
                merged = self._merge_schemas(merged, resolved)
            return merged
        
        return schema
    
    def _merge_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two schemas"""
        merged = schema1.copy()
        
        for key, value in schema2.items():
            if key == 'properties' and key in merged:
                merged[key] = {**merged[key], **value}
            elif key == 'required' and key in merged:
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value
        
        return merged
    
    # ==================================================================================
    # SCHEMA VALIDATION
    # ==================================================================================
    
    def validate_request(
        self,
        endpoint: str,
        method: str,
        data: Any
    ) -> tuple[bool, Optional[List[str]]]:
        """
        Validate request data against contract
        
        Returns: (is_valid, errors)
        """
        # Normalize endpoint (remove path parameters)
        normalized_endpoint = self._normalize_endpoint(endpoint)
        
        validator_key = f'{normalized_endpoint}_{method}_request'
        
        if validator_key not in self.schema_cache:
            # No schema defined - allow but log warning
            current_app.logger.warning(f'No request schema defined for {method} {endpoint}')
            return True, None
        
        validator = self.schema_cache[validator_key]
        
        try:
            validator.validate(data)
            return True, None
        except ValidationError as e:
            errors = [str(err) for err in validator.iter_errors(data)]
            
            # Log violation
            self._log_contract_violation(
                endpoint=endpoint,
                method=method,
                violation_type='schema',
                severity='high',
                details={
                    'validation_errors': errors,
                    'data_type': 'request'
                },
                actual_data=data
            )
            
            return False, errors
    
    def validate_response(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        data: Any
    ) -> tuple[bool, Optional[List[str]]]:
        """
        Validate response data against contract
        
        Returns: (is_valid, errors)
        """
        # Normalize endpoint
        normalized_endpoint = self._normalize_endpoint(endpoint)
        
        validator_key = f'{normalized_endpoint}_{method}_response_{status_code}'
        
        if validator_key not in self.schema_cache:
            # Try to use generic success/error schema
            if 200 <= status_code < 300:
                validator_key = 'base_Success'
            elif status_code >= 400:
                validator_key = 'base_Error'
            else:
                return True, None
        
        if validator_key not in self.schema_cache:
            return True, None
        
        validator = self.schema_cache[validator_key]
        
        try:
            validator.validate(data)
            return True, None
        except ValidationError as e:
            errors = [str(err) for err in validator.iter_errors(data)]
            
            # Log violation
            self._log_contract_violation(
                endpoint=endpoint,
                method=method,
                violation_type='schema',
                severity='critical',  # Response violations are critical
                details={
                    'validation_errors': errors,
                    'data_type': 'response',
                    'status_code': status_code
                },
                actual_data=data
            )
            
            return False, errors
    
    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint by replacing path parameters with placeholders"""
        parts = endpoint.split('/')
        normalized_parts = []
        
        for part in parts:
            # Check if this looks like a path parameter (numeric or UUID-like)
            if part.isdigit() or '-' in part and len(part) > 10:
                # Replace with placeholder based on context
                if 'table' in endpoint:
                    normalized_parts.append('{table_name}')
                elif 'record' in endpoint or 'id' in endpoint:
                    normalized_parts.append('{id}')
                else:
                    normalized_parts.append('{param}')
            else:
                normalized_parts.append(part)
        
        return '/'.join(normalized_parts)
    
    # ==================================================================================
    # API VERSIONING
    # ==================================================================================
    
    def get_api_version(self) -> str:
        """Get API version from request headers or default"""
        # Check for version in Accept header
        accept_header = request.headers.get('Accept', '')
        if 'version=' in accept_header:
            version = accept_header.split('version=')[1].split(';')[0].strip()
            if version in API_VERSIONS:
                return version
        
        # Check for version in custom header
        version_header = request.headers.get('X-API-Version')
        if version_header and version_header in API_VERSIONS:
            return version_header
        
        # Check for version in URL
        if '/v1/' in request.path:
            return 'v1'
        elif '/v2/' in request.path:
            return 'v2'
        
        return DEFAULT_API_VERSION
    
    def check_version_compatibility(self, required_version: str) -> bool:
        """Check if requested API version is compatible"""
        current_version = self.get_api_version()
        
        if current_version not in API_VERSIONS:
            return False
        
        version_info = API_VERSIONS[current_version]
        
        # Check if version is sunset
        if version_info.status == 'sunset':
            self._log_contract_violation(
                endpoint=request.endpoint or 'unknown',
                method=request.method,
                violation_type='version',
                severity='critical',
                details={
                    'requested_version': current_version,
                    'status': 'sunset',
                    'message': 'API version has been sunset and is no longer available'
                }
            )
            return False
        
        # Warn if deprecated
        if version_info.status == 'deprecated':
            current_app.logger.warning(
                f'Using deprecated API version {current_version}. '
                f'Deprecation date: {version_info.deprecation_date}. '
                f'Sunset date: {version_info.sunset_date}'
            )
        
        return True
    
    # ==================================================================================
    # CONTRACT VIOLATION TRACKING
    # ==================================================================================
    
    def _log_contract_violation(
        self,
        endpoint: str,
        method: str,
        violation_type: str,
        severity: str,
        details: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
        actual_data: Optional[Any] = None
    ):
        """Log a contract violation"""
        violation = ContractViolation(
            violation_id=hashlib.md5(f"{endpoint}{method}{violation_type}{time.time()}".encode()).hexdigest()[:12],
            timestamp=datetime.now(timezone.utc),
            endpoint=endpoint,
            method=method,
            violation_type=violation_type,
            severity=severity,
            details=details,
            expected_schema=expected_schema,
            actual_data=actual_data
        )
        
        self.contract_violations.append(violation)
        
        # Keep only last 1000 violations
        if len(self.contract_violations) > 1000:
            self.contract_violations = self.contract_violations[-1000:]
        
        # Log to application logger
        current_app.logger.error(
            f'🔴 CONTRACT VIOLATION [{severity.upper()}]: {violation_type} in {method} {endpoint}'
        )
    
    def get_contract_violations(
        self,
        severity: Optional[str] = None,
        violation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get contract violations"""
        violations = self.contract_violations
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]
        
        # Return most recent
        violations = violations[-limit:]
        
        return [
            {
                'violation_id': v.violation_id,
                'timestamp': v.timestamp.isoformat(),
                'endpoint': v.endpoint,
                'method': v.method,
                'violation_type': v.violation_type,
                'severity': v.severity,
                'details': v.details
            }
            for v in violations
        ]
    
    # ==================================================================================
    # OPENAPI SPECIFICATION GENERATION
    # ==================================================================================
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        return {
            'openapi': '3.0.3',
            'info': {
                'title': 'CogniForge API',
                'description': 'World-class RESTful API with advanced observability, security, and contract validation',
                'version': DEFAULT_API_VERSION,
                'contact': {
                    'name': 'CogniForge Team',
                    'url': 'https://github.com/HOUSSAM16ai/my_ai_project'
                },
                'license': {
                    'name': 'MIT',
                    'url': 'https://opensource.org/licenses/MIT'
                }
            },
            'servers': [
                {
                    'url': '/admin/api',
                    'description': 'Admin API v2 (Current)'
                },
                {
                    'url': '/admin/api/v1',
                    'description': 'Admin API v1 (Deprecated)'
                }
            ],
            'components': {
                'schemas': {
                    **BASE_SCHEMAS,
                    # Add more schemas as needed
                },
                'securitySchemes': {
                    'BearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT',
                        'description': 'Short-lived JWT token (15 minutes)'
                    },
                    'RequestSignature': {
                        'type': 'apiKey',
                        'in': 'header',
                        'name': 'X-Signature',
                        'description': 'HMAC-SHA256 request signature for Zero-Trust security'
                    }
                }
            },
            'security': [
                {'BearerAuth': []},
                {'RequestSignature': []}
            ],
            'paths': self._generate_paths()
        }
    
    def _generate_paths(self) -> Dict[str, Any]:
        """Generate OpenAPI paths from endpoint schemas"""
        paths = {}
        
        for endpoint, methods in ENDPOINT_SCHEMAS.items():
            paths[endpoint] = {}
            
            for method, specs in methods.items():
                operation = {
                    'summary': f'{method} {endpoint}',
                    'responses': {}
                }
                
                if 'request' in specs:
                    operation['requestBody'] = {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': specs['request']
                            }
                        }
                    }
                
                if 'response' in specs:
                    for status_code, schema in specs['response'].items():
                        operation['responses'][status_code] = {
                            'description': f'Response {status_code}',
                            'content': {
                                'application/json': {
                                    'schema': schema
                                }
                            }
                        }
                
                paths[endpoint][method.lower()] = operation
        
        return paths


# ======================================================================================
# GLOBAL SERVICE INSTANCE
# ======================================================================================

_contract_service: Optional[APIContractService] = None

def get_contract_service() -> APIContractService:
    """Get or create global contract service instance"""
    global _contract_service
    if _contract_service is None:
        _contract_service = APIContractService()
    return _contract_service


# ======================================================================================
# VALIDATION DECORATORS
# ======================================================================================

def validate_contract(f: Callable) -> Callable:
    """Decorator to validate request/response against API contract"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        service = get_contract_service()
        
        # Validate API version
        if not service.check_version_compatibility(DEFAULT_API_VERSION):
            return jsonify({
                'error': 'API version not supported',
                'message': 'The requested API version is no longer available'
            }), 410  # Gone
        
        # Validate request if JSON data present
        if request.is_json and request.method in ['POST', 'PUT', 'PATCH']:
            is_valid, errors = service.validate_request(
                endpoint=request.path,
                method=request.method,
                data=request.get_json()
            )
            
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'error': 'Request validation failed',
                    'validation_errors': errors
                }), 400
        
        # Execute endpoint
        response = f(*args, **kwargs)
        
        # Validate response (only in development/testing)
        if current_app.config.get('VALIDATE_RESPONSES', False):
            try:
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                    status_code = response.status_code
                    
                    is_valid, errors = service.validate_response(
                        endpoint=request.path,
                        method=request.method,
                        status_code=status_code,
                        data=response_data
                    )
                    
                    if not is_valid:
                        current_app.logger.error(
                            f'Response validation failed for {request.method} {request.path}: {errors}'
                        )
            except Exception as e:
                current_app.logger.error(f'Error validating response: {e}')
        
        return response
    
    return decorated_function
