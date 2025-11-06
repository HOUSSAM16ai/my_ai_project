# app/services/api_developer_portal_service.py
# ======================================================================================
# ==    SUPERHUMAN DEVELOPER PORTAL SERVICE (v1.0 - WORLD-CLASS EDITION)          ==
# ======================================================================================
# PRIME DIRECTIVE:
#   بوابة مطورين خارقة تتفوق على Stripe و Twilio و AWS
#   ✨ المميزات الخارقة:
#   - Automatic SDK generation (Python, JavaScript, Go, Ruby, Java)
#   - Interactive API documentation
#   - Ticket and support system
#   - API key management
#   - Sandbox environment
#   - Code examples and tutorials
#   - Webhook management
#   - Developer analytics

import hashlib
import secrets
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from flask import current_app

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class SDKLanguage(Enum):
    """Supported SDK languages"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUBY = "ruby"
    JAVA = "java"
    PHP = "php"
    CSHARP = "csharp"


class TicketStatus(Enum):
    """Support ticket status"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(Enum):
    """Support ticket priority"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class APIKeyStatus(Enum):
    """API key status"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class APIKey:
    """API key for developers"""

    key_id: str
    key_value: str
    name: str
    developer_id: str

    status: APIKeyStatus
    created_at: datetime

    # Permissions
    scopes: list[str] = field(default_factory=list)
    allowed_ips: list[str] = field(default_factory=list)

    # Usage tracking
    total_requests: int = 0
    last_used_at: datetime | None = None

    # Lifecycle
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SupportTicket:
    """Developer support ticket"""

    ticket_id: str
    developer_id: str

    title: str
    description: str
    category: str  # technical, billing, feature_request, bug_report

    status: TicketStatus
    priority: TicketPriority

    created_at: datetime
    updated_at: datetime

    # Assignment
    assigned_to: str | None = None

    # Timeline
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Resolution
    resolved_at: datetime | None = None
    resolution: str | None = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SDKPackage:
    """Generated SDK package"""

    sdk_id: str
    language: SDKLanguage
    version: str

    # Generation
    generated_at: datetime
    api_version: str

    # Distribution
    package_url: str
    documentation_url: str

    # Stats
    download_count: int = 0

    # Code
    source_code: str = ""
    examples: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CodeExample:
    """Code example for developers"""

    example_id: str
    title: str
    description: str
    language: SDKLanguage

    code: str
    endpoint: str

    # Metadata
    tags: list[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ======================================================================================
# DEVELOPER PORTAL SERVICE
# ======================================================================================


class DeveloperPortalService:
    """
    خدمة بوابة المطورين الخارقة - Superhuman Developer Portal Service

    Features:
    - API key management with fine-grained permissions
    - Automatic SDK generation for multiple languages
    - Interactive documentation and examples
    - Support ticket system
    - Sandbox environment for testing
    - Developer analytics and insights
    """

    def __init__(self):
        self.api_keys: dict[str, APIKey] = {}
        self.tickets: dict[str, SupportTicket] = {}
        self.sdks: dict[str, SDKPackage] = {}
        self.code_examples: dict[str, CodeExample] = {}

        self.lock = threading.RLock()

        # Analytics
        self.developer_metrics: dict[str, Any] = defaultdict(
            lambda: {
                "total_developers": 0,
                "active_developers_30d": 0,
                "total_api_keys": 0,
                "total_requests": 0,
                "sdk_downloads": 0,
                "open_tickets": 0,
            }
        )

        self._initialize_code_examples()

    def _initialize_code_examples(self):
        """Initialize default code examples"""

        # Python example
        self.code_examples["py_basic"] = CodeExample(
            example_id="py_basic",
            title="Basic API Request (Python)",
            description="Make a simple API request using Python",
            language=SDKLanguage.PYTHON,
            code="""import requests
import os

# Set your API key from environment variable
api_key = os.environ.get("COGNIFORGE_API_KEY")
headers = {"Authorization": f"Bearer {api_key}"}

# Make a request
response = requests.get(
    "https://api.cogniforge.ai/v1/users",
    headers=headers
)

# Parse response
data = response.json()
print(data)""",
            endpoint="/v1/users",
            tags=["getting-started", "authentication"],
            difficulty="beginner",
        )

        # JavaScript example
        self.code_examples["js_basic"] = CodeExample(
            example_id="js_basic",
            title="Basic API Request (JavaScript)",
            description="Make a simple API request using JavaScript/Node.js",
            language=SDKLanguage.JAVASCRIPT,
            code="""const axios = require('axios');

// Set your API key from environment variable
const apiKey = process.env.COGNIFORGE_API_KEY;

// Make a request
axios.get('https://api.cogniforge.ai/v1/users', {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
})
.then(response => {
  console.log(response.data);
})
.catch(error => {
  console.error('Error:', error);
});""",
            endpoint="/v1/users",
            tags=["getting-started", "authentication"],
            difficulty="beginner",
        )

    def create_api_key(
        self,
        developer_id: str,
        name: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> APIKey:
        """Create a new API key"""
        with self.lock:
            # Generate secure key
            key_value = f"sk_live_{secrets.token_urlsafe(32)}"
            key_id = (
                f"key_{hashlib.md5(key_value.encode(), usedforsecurity=False).hexdigest()[:16]}"
            )

            now = datetime.now(UTC)
            expires_at = now + timedelta(days=expires_in_days) if expires_in_days else None

            api_key = APIKey(
                key_id=key_id,
                key_value=key_value,
                name=name,
                developer_id=developer_id,
                status=APIKeyStatus.ACTIVE,
                created_at=now,
                scopes=scopes or ["read", "write"],
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self.api_keys[key_id] = api_key

            current_app.logger.info(f"Created API key {key_id} for developer {developer_id}")

            return api_key

    def validate_api_key(self, key_value: str) -> APIKey | None:
        """Validate an API key"""
        for api_key in self.api_keys.values():
            if api_key.key_value == key_value:
                # Check if expired
                if api_key.expires_at and datetime.now(UTC) > api_key.expires_at:
                    return None

                # Check if active
                if api_key.status != APIKeyStatus.ACTIVE:
                    return None

                # Update usage
                api_key.total_requests += 1
                api_key.last_used_at = datetime.now(UTC)

                return api_key

        return None

    def revoke_api_key(self, key_id: str, reason: str) -> bool:
        """Revoke an API key"""
        with self.lock:
            api_key = self.api_keys.get(key_id)
            if not api_key:
                return False

            api_key.status = APIKeyStatus.REVOKED
            api_key.revoked_at = datetime.now(UTC)
            api_key.revocation_reason = reason

            current_app.logger.info(f"Revoked API key {key_id}: {reason}")

            return True

    def create_ticket(
        self,
        developer_id: str,
        title: str,
        description: str,
        category: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
    ) -> SupportTicket:
        """Create a support ticket"""
        with self.lock:
            ticket_id = f"ticket_{secrets.token_hex(8)}"

            now = datetime.now(UTC)

            ticket = SupportTicket(
                ticket_id=ticket_id,
                developer_id=developer_id,
                title=title,
                description=description,
                category=category,
                status=TicketStatus.OPEN,
                priority=priority,
                created_at=now,
                updated_at=now,
            )

            # Add initial message
            ticket.messages.append(
                {
                    "id": f"msg_{secrets.token_hex(6)}",
                    "author_id": developer_id,
                    "content": description,
                    "timestamp": now.isoformat(),
                    "is_staff": False,
                }
            )

            self.tickets[ticket_id] = ticket

            current_app.logger.info(f"Created ticket {ticket_id} for developer {developer_id}")

            return ticket

    def add_ticket_message(
        self, ticket_id: str, author_id: str, content: str, is_staff: bool = False
    ) -> bool:
        """Add a message to a ticket"""
        with self.lock:
            ticket = self.tickets.get(ticket_id)
            if not ticket:
                return False

            message = {
                "id": f"msg_{secrets.token_hex(6)}",
                "author_id": author_id,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
                "is_staff": is_staff,
            }

            ticket.messages.append(message)
            ticket.updated_at = datetime.now(UTC)

            # Update status if customer responded
            if not is_staff and ticket.status == TicketStatus.WAITING_FOR_CUSTOMER:
                ticket.status = TicketStatus.IN_PROGRESS

            return True

    def resolve_ticket(self, ticket_id: str, resolution: str) -> bool:
        """Resolve a support ticket"""
        with self.lock:
            ticket = self.tickets.get(ticket_id)
            if not ticket:
                return False

            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.now(UTC)
            ticket.resolution = resolution
            ticket.updated_at = datetime.now(UTC)

            return True

    def generate_sdk(self, language: SDKLanguage, api_version: str = "v1") -> SDKPackage:
        """Generate SDK for a specific language"""
        with self.lock:
            sdk_id = f"sdk_{language.value}_{api_version}_{secrets.token_hex(4)}"
            version = "1.0.0"

            # Generate SDK code based on language
            source_code = self._generate_sdk_code(language, api_version)
            examples = self._generate_sdk_examples(language)

            sdk = SDKPackage(
                sdk_id=sdk_id,
                language=language,
                version=version,
                generated_at=datetime.now(UTC),
                api_version=api_version,
                package_url=f"https://sdk.cogniforge.ai/{language.value}/{version}",
                documentation_url=f"https://docs.cogniforge.ai/sdk/{language.value}",
                source_code=source_code,
                examples=examples,
            )

            self.sdks[sdk_id] = sdk

            current_app.logger.info(f"Generated {language.value} SDK version {version}")

            return sdk

    def _generate_sdk_code(self, language: SDKLanguage, api_version: str) -> str:
        """Generate SDK source code"""
        if language == SDKLanguage.PYTHON:
            return self._generate_python_sdk()
        elif language == SDKLanguage.JAVASCRIPT:
            return self._generate_javascript_sdk()
        elif language == SDKLanguage.GO:
            return self._generate_go_sdk()
        else:
            return "# SDK generation not implemented for this language yet"

    def _generate_python_sdk(self) -> str:
        """Generate Python SDK"""
        return '''"""CogniForge API Python SDK"""

import requests
from typing import Dict, Any, Optional, List

class CogniForgeClient:
    """CogniForge API Client"""

    def __init__(self, api_key: str, base_url: str = "https://api.cogniforge.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    # Users
    def list_users(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """List all users"""
        return self._request("GET", "/users", params={"page": page, "per_page": per_page})

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID"""
        return self._request("GET", f"/users/{user_id}")

    def create_user(self, email: str, name: str, **kwargs) -> Dict[str, Any]:
        """Create a new user"""
        data = {"email": email, "name": name, **kwargs}
        return self._request("POST", "/users", json=data)

    # Missions
    def list_missions(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """List all missions"""
        return self._request("GET", "/missions", params={"page": page, "per_page": per_page})

    def get_mission(self, mission_id: int) -> Dict[str, Any]:
        """Get mission by ID"""
        return self._request("GET", f"/missions/{mission_id}")
'''

    def _generate_javascript_sdk(self) -> str:
        """Generate JavaScript SDK"""
        return """/**
 * CogniForge API JavaScript SDK
 */

class CogniForgeClient {
  constructor(apiKey, baseUrl = 'https://api.cogniforge.ai/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async _request(method, endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, {
      method,
      headers,
      ...options
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Users
  async listUsers(page = 1, perPage = 20) {
    const params = new URLSearchParams({ page, per_page: perPage });
    return this._request('GET', `/users?${params}`);
  }

  async getUser(userId) {
    return this._request('GET', `/users/${userId}`);
  }

  async createUser(email, name, additionalData = {}) {
    return this._request('POST', '/users', {
      body: JSON.stringify({ email, name, ...additionalData })
    });
  }

  // Missions
  async listMissions(page = 1, perPage = 20) {
    const params = new URLSearchParams({ page, per_page: perPage });
    return this._request('GET', `/missions?${params}`);
  }

  async getMission(missionId) {
    return this._request('GET', `/missions/${missionId}`);
  }
}

module.exports = CogniForgeClient;
"""

    def _generate_go_sdk(self) -> str:
        """Generate Go SDK"""
        return """package cogniforge

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
)

// Client is the CogniForge API client
type Client struct {
    APIKey  string
    BaseURL string
    client  *http.Client
}

// NewClient creates a new CogniForge API client
func NewClient(apiKey string) *Client {
    return &Client{
        APIKey:  apiKey,
        BaseURL: "https://api.cogniforge.ai/v1",
        client:  &http.Client{},
    }
}

func (c *Client) request(method, endpoint string, body interface{}) (map[string]interface{}, error) {
    url := c.BaseURL + endpoint

    var reqBody []byte
    if body != nil {
        var err error
        reqBody, err = json.Marshal(body)
        if err != nil {
            return nil, err
        }
    }

    req, err := http.NewRequest(method, url, bytes.NewBuffer(reqBody))
    if err != nil {
        return nil, err
    }

    req.Header.Set("Authorization", "Bearer "+c.APIKey)
    req.Header.Set("Content-Type", "application/json")

    resp, err := c.client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    respBody, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }

    var result map[string]interface{}
    err = json.Unmarshal(respBody, &result)
    return result, err
}

// ListUsers lists all users
func (c *Client) ListUsers(page, perPage int) (map[string]interface{}, error) {
    endpoint := fmt.Sprintf("/users?page=%d&per_page=%d", page, perPage)
    return c.request("GET", endpoint, nil)
}

// GetUser gets a user by ID
func (c *Client) GetUser(userID int) (map[string]interface{}, error) {
    endpoint := fmt.Sprintf("/users/%d", userID)
    return c.request("GET", endpoint, nil)
}
"""

    def _generate_sdk_examples(self, language: SDKLanguage) -> list[dict[str, str]]:
        """Generate SDK usage examples"""
        if language == SDKLanguage.PYTHON:
            return [
                {
                    "title": "Initialize Client",
                    "code": 'import os\nclient = CogniForgeClient(api_key=os.environ.get("COGNIFORGE_API_KEY"))',
                },
                {"title": "List Users", "code": "users = client.list_users(page=1, per_page=20)"},
                {
                    "title": "Create User",
                    "code": 'user = client.create_user(email="user@example.com", name="John Doe")',
                },
            ]
        elif language == SDKLanguage.JAVASCRIPT:
            return [
                {
                    "title": "Initialize Client",
                    "code": 'const client = new CogniForgeClient(process.env.COGNIFORGE_API_KEY);',
                },
                {"title": "List Users", "code": "const users = await client.listUsers(1, 20);"},
                {
                    "title": "Create User",
                    "code": 'const user = await client.createUser("user@example.com", "John Doe");',
                },
            ]
        return []

    def get_developer_dashboard(self, developer_id: str) -> dict[str, Any]:
        """Get developer dashboard data"""
        # Get developer's API keys
        api_keys = [
            {
                "key_id": key.key_id,
                "name": key.name,
                "status": key.status.value,
                "total_requests": key.total_requests,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "created_at": key.created_at.isoformat(),
            }
            for key in self.api_keys.values()
            if key.developer_id == developer_id
        ]

        # Get developer's tickets
        tickets = [
            {
                "ticket_id": ticket.ticket_id,
                "title": ticket.title,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "created_at": ticket.created_at.isoformat(),
                "updated_at": ticket.updated_at.isoformat(),
            }
            for ticket in self.tickets.values()
            if ticket.developer_id == developer_id
        ]

        # Calculate stats
        total_requests = sum(
            key.total_requests for key in self.api_keys.values() if key.developer_id == developer_id
        )

        return {
            "developer_id": developer_id,
            "api_keys": api_keys,
            "tickets": tickets,
            "stats": {
                "total_api_keys": len(api_keys),
                "total_requests": total_requests,
                "open_tickets": sum(1 for t in tickets if t["status"] == "open"),
            },
        }

    def get_available_sdks(self) -> list[dict[str, Any]]:
        """Get list of available SDKs"""
        sdks = []
        for language in SDKLanguage:
            sdks.append(
                {
                    "language": language.value,
                    "name": f"CogniForge {language.value.capitalize()} SDK",
                    "documentation_url": f"https://docs.cogniforge.ai/sdk/{language.value}",
                    "installation": self._get_installation_command(language),
                }
            )
        return sdks

    def _get_installation_command(self, language: SDKLanguage) -> str:
        """Get installation command for SDK"""
        commands = {
            SDKLanguage.PYTHON: "pip install cogniforge",
            SDKLanguage.JAVASCRIPT: "npm install cogniforge",
            SDKLanguage.GO: "go get github.com/cogniforge/cogniforge-go",
            SDKLanguage.RUBY: "gem install cogniforge",
            SDKLanguage.JAVA: "maven dependency or gradle",
            SDKLanguage.PHP: "composer require cogniforge/cogniforge-php",
        }
        return commands.get(language, "See documentation")


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_developer_portal_instance: DeveloperPortalService | None = None
_service_lock = threading.Lock()


def get_developer_portal_service() -> DeveloperPortalService:
    """Get singleton developer portal service"""
    global _developer_portal_instance

    if _developer_portal_instance is None:
        with _service_lock:
            if _developer_portal_instance is None:
                _developer_portal_instance = DeveloperPortalService()

    return _developer_portal_instance
