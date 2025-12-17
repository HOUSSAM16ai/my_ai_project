from __future__ import annotations
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class FrontendFramework(Enum):
    """Frontend frameworks"""
    REACT = 'react'
    VUE = 'vue'
    ANGULAR = 'angular'
    SVELTE = 'svelte'
    VANILLA = 'vanilla'


class ModuleType(Enum):
    """Micro frontend module types"""
    SHELL = 'shell'
    REMOTE = 'remote'
    SHARED = 'shared'


@dataclass
class MicroFrontend:
    """Micro frontend module definition"""
    module_id: str
    name: str
    module_type: ModuleType
    framework: FrontendFramework
    entry_url: str
    exposed_modules: dict[str, str]
    shared_dependencies: list[str]
    owner_team: str
    version: str
    created_at: datetime = field(default_factory=lambda : datetime.now(UTC))
    active: bool = True


@dataclass
class ModuleFederation:
    """Module federation configuration"""
    federation_id: str
    shell_module_id: str
    remote_modules: list[str]
    shared_state_keys: list[str]
    routing_config: dict[str, str]
    created_at: datetime = field(default_factory=lambda : datetime.now(UTC))


@dataclass
class SharedState:
    """Shared state between micro frontends"""
    state_id: str
    key: str
    value: Any
    owner_module_id: str
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))


class MicroFrontendsService:
    """
    خدمة Micro Frontends الخارقة - World-class micro frontends

    Features:
    - Module federation support
    - Independent deployment
    - Framework agnostic architecture
    - Shared state management
    - Dynamic module loading
    """

    def __init__(self):
        self.modules: dict[str, MicroFrontend] = {}
        self.federations: dict[str, ModuleFederation] = {}
        self.shared_state: dict[str, SharedState] = {}
        self.module_versions: dict[str, list[str]] = defaultdict(list)
        self.lock = threading.RLock()
        logging.getLogger(__name__).info('Micro Frontends Service initialized')

    def register_module(self, module: MicroFrontend) ->bool:
        """Register micro frontend module"""
        with self.lock:
            self.modules[module.module_id] = module
            self.module_versions[module.name].append(module.version)
            logging.getLogger(__name__).info(
                f'Registered micro frontend: {module.name} ({module.framework.value})'
                )
            return True

    def get_module(self, module_id: str) ->(MicroFrontend | None):
        """Get module by ID"""
        return self.modules.get(module_id)

    def get_modules_by_framework(self, framework: FrontendFramework) ->list[
        MicroFrontend]:
        """Get modules by framework"""
        return [m for m in self.modules.values() if m.framework == framework]

    def create_federation(self, federation: ModuleFederation) ->bool:
        """Create module federation"""
        with self.lock:
            self.federations[federation.federation_id] = federation
            logging.getLogger(__name__).info(
                f'Created module federation with {len(federation.remote_modules)} remotes'
                )
            return True

    def get_federation_config(self, federation_id: str) ->(dict[str, Any] |
        None):
        """Get federation configuration for deployment"""
        federation = self.federations.get(federation_id)
        if not federation:
            return None
        shell_module = self.modules.get(federation.shell_module_id)
        if not shell_module:
            return None
        remotes = {}
        for remote_id in federation.remote_modules:
            remote_module = self.modules.get(remote_id)
            if remote_module:
                remotes[remote_module.name] = {'url': remote_module.
                    entry_url, 'exposed': remote_module.exposed_modules}
        return {'name': shell_module.name, 'remotes': remotes, 'shared':
            self._get_shared_dependencies(federation), 'routing':
            federation.routing_config}

    def _get_shared_dependencies(self, federation: ModuleFederation) ->dict[
        str, Any]:
        """Get shared dependencies configuration"""
        all_modules = [self.modules.get(federation.shell_module_id)] + [self
            .modules.get(r) for r in federation.remote_modules]
        shared_deps = set()
        for module in all_modules:
            if module:
                shared_deps.update(module.shared_dependencies)
        return {dep: {'singleton': True} for dep in shared_deps}

    def get_shared_state(self, key: str) ->(Any | None):
        """Get shared state value"""
        state = self.shared_state.get(key)
        return state.value if state else None

    def get_metrics(self) ->dict[str, Any]:
        """Get micro frontends metrics"""
        return {'total_modules': len(self.modules), 'active_modules': len([
            m for m in self.modules.values() if m.active]),
            'modules_by_framework': {fw.value: len([m for m in self.modules
            .values() if m.framework == fw]) for fw in FrontendFramework},
            'module_types': {mt.value: len([m for m in self.modules.values(
            ) if m.module_type == mt]) for mt in ModuleType},
            'total_federations': len(self.federations), 'shared_state_keys':
            len(self.shared_state)}


_micro_frontends_instance: MicroFrontendsService | None = None
_mf_lock = threading.Lock()


def get_micro_frontends_service() ->MicroFrontendsService:
    """Get singleton micro frontends service instance"""
    global _micro_frontends_instance
    if _micro_frontends_instance is None:
        with _mf_lock:
            if _micro_frontends_instance is None:
                _micro_frontends_instance = MicroFrontendsService()
    return _micro_frontends_instance
