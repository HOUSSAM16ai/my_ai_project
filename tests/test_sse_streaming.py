"""
Test SSE Streaming Implementation
===================================
Tests for the robust SSE streaming endpoints and consumer.

Run with: pytest tests/test_sse_streaming.py -v
"""

import json
import pytest
from flask import Flask


def parse_sse_events(data):
    """Parse SSE response data into events"""
    events = []
    current_event = {"event": "message", "data": [], "id": None}
    
    for line in data.decode('utf-8').split('\n'):
        if line.startswith('event:'):
            current_event['event'] = line[6:].strip()
        elif line.startswith('data:'):
            current_event['data'].append(line[5:].strip())
        elif line.startswith('id:'):
            current_event['id'] = line[3:].strip()
        elif line == '':
            # End of event
            if current_event['data']:
                # Join multi-line data
                data_str = '\n'.join(current_event['data'])
                try:
                    current_event['data'] = json.loads(data_str)
                except json.JSONDecodeError:
                    current_event['data'] = data_str
                
                events.append(current_event.copy())
                current_event = {"event": "message", "data": [], "id": None}
    
    return events


class TestSSEStreamRoutes:
    """Test the new SSE streaming routes"""
    
    def test_stream_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get('/api/v1/stream/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['service'] == 'sse-streaming'
        assert 'endpoints' in data
    
    def test_sse_chat_requires_question(self, client, auth_headers):
        """Test that SSE chat requires a question parameter"""
        response = client.get('/api/v1/stream/chat', headers=auth_headers)
        
        # Should get an error event
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream; charset=utf-8'
        
        events = parse_sse_events(response.data)
        assert len(events) > 0
        assert events[0]['event'] == 'error'
    
    def test_sse_chat_headers(self, client, auth_headers):
        """Test that SSE endpoint returns correct headers"""
        response = client.get(
            '/api/v1/stream/chat?q=test',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert 'text/event-stream' in response.content_type
        assert response.headers.get('Cache-Control') == 'no-cache, no-transform'
        assert response.headers.get('X-Accel-Buffering') == 'no'
    
    def test_sse_chat_event_format(self, client, auth_headers):
        """Test that SSE events are properly formatted"""
        response = client.get(
            '/api/v1/stream/chat?q=test',
            headers=auth_headers
        )
        
        events = parse_sse_events(response.data)
        
        # Should have at least hello, delta, and done events
        event_types = [e['event'] for e in events]
        assert 'hello' in event_types
        assert 'done' in event_types
        
        # Check hello event structure
        hello_events = [e for e in events if e['event'] == 'hello']
        if hello_events:
            hello_data = hello_events[0]['data']
            assert 'ts' in hello_data
            assert 'model' in hello_data


class TestAdminStreamRoutes:
    """Test the updated admin streaming routes"""
    
    def test_admin_stream_requires_auth(self, client):
        """Test that admin stream requires authentication"""
        response = client.get('/admin/api/chat/stream?question=test')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]
    
    def test_admin_stream_headers(self, client, admin_auth_headers):
        """Test that admin stream endpoint returns correct headers"""
        response = client.get(
            '/admin/api/chat/stream?question=test',
            headers=admin_auth_headers
        )
        
        # Check SSE headers
        assert 'text/event-stream' in response.content_type
        assert 'no-cache' in response.headers.get('Cache-Control', '')
        assert response.headers.get('X-Accel-Buffering') == 'no'


class TestSSEEventFormatting:
    """Test SSE event formatting utilities"""
    
    def test_sse_event_basic(self):
        """Test basic SSE event formatting"""
        from app.api.stream_routes import sse_event
        
        result = sse_event("test", {"message": "hello"})
        
        assert "event: test\n" in result
        assert "data: " in result
        assert "\n\n" in result  # Blank line separator
    
    def test_sse_event_with_id(self):
        """Test SSE event with ID"""
        from app.api.stream_routes import sse_event
        
        result = sse_event("test", {"message": "hello"}, eid="123")
        
        assert "event: test\n" in result
        assert "id: 123\n" in result
    
    def test_sse_event_multiline_data(self):
        """Test SSE event with multiline data"""
        from app.api.stream_routes import sse_event
        
        result = sse_event("test", "line1\nline2\nline3")
        
        # Each line should be prefixed with "data: "
        assert "data: line1\n" in result
        assert "data: line2\n" in result
        assert "data: line3\n" in result


class TestStreamingService:
    """Test the admin chat streaming service"""
    
    def test_streaming_service_initialization(self):
        """Test that streaming service can be initialized"""
        try:
            from app.services.admin_chat_streaming_service import get_streaming_service
            
            service = get_streaming_service()
            assert service is not None
            assert hasattr(service, 'stream_response')
        except ImportError:
            pytest.skip("Streaming service not available")
    
    def test_streaming_service_format(self):
        """Test streaming service SSE formatting"""
        try:
            from app.services.admin_chat_streaming_service import get_streaming_service
            
            service = get_streaming_service()
            
            # Test streaming a simple message
            events = list(service.stream_response("Hello world", {"test": True}))
            
            # Should have events
            assert len(events) > 0
            
            # All events should contain "event:" and "data:"
            for event in events:
                assert "event:" in event or "data:" in event
                
        except ImportError:
            pytest.skip("Streaming service not available")


# Fixtures
@pytest.fixture
def app():
    """Create test Flask app"""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for regular user"""
    # This is a placeholder - implement based on your auth system
    return {
        'Authorization': 'Bearer test_token'
    }


@pytest.fixture
def admin_auth_headers(client):
    """Create authentication headers for admin user"""
    # This is a placeholder - implement based on your auth system
    return {
        'Authorization': 'Bearer admin_token'
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
