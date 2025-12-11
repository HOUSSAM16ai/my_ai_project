# Cosmic Governance Service - Hexagonal Architecture

## Overview

Refactored Cosmic Governance service from monolithic design to Hexagonal Architecture (Ports & Adapters).

**Original**: 714 lines / 26KB monolithic service  
**New**: 12 specialized files with clear separation of concerns

## Architecture

```
app/services/governance/
│
├── __init__.py                    # Public API
├── facade.py                      # Backward compatible facade
├── README.md                      # This file
│
├── domain/                        # Domain Layer
│   ├── __init__.py
│   ├── models.py                  # Domain entities
│   └── ports.py                   # Interfaces/Protocols
│
├── application/                   # Application Layer
│   ├── __init__.py
│   ├── protocol_manager.py        # Protocol management
│   ├── council_manager.py         # Council management
│   ├── consciousness_manager.py   # Consciousness operations
│   └── transparency_service.py    # Transparency logging
│
└── infrastructure/                # Infrastructure Layer
    ├── __init__.py
    └── sqlalchemy_repositories.py # Database adapters
```

## Components

### Domain Layer

**models.py** - Domain entities (references to SQLAlchemy models):
- `ExistentialProtocol`: Cosmic protocols
- `CosmicGovernanceCouncil`: Governance councils
- `ConsciousnessSignature`: Consciousness entities
- `ExistentialTransparencyLog`: Transparency records

**ports.py** - Interfaces:
- `ProtocolRepositoryPort`: Protocol storage
- `CouncilRepositoryPort`: Council storage
- `ConsciousnessRepositoryPort`: Consciousness storage
- `TransparencyRepositoryPort`: Transparency logging

### Application Layer

**protocol_manager.py** - Protocol Management
- Create existential protocols
- Activate protocols
- Opt-in to protocols
- Check compliance

**council_manager.py** - Council Management
- Create cosmic councils
- Add council members
- Propose decisions
- Vote on decisions

**consciousness_manager.py** - Consciousness Operations
- Consciousness consensus
- Auto-realignment
- Understanding verification

**transparency_service.py** - Transparency Logging
- Log governance events
- Query transparency logs
- Audit trail

### Infrastructure Layer

**sqlalchemy_repositories.py** - Database Adapters
- SQLAlchemy implementations of all repository ports
- Transaction management
- Database operations

## Usage

### Basic Usage (Backward Compatible)

```python
from app.services.governance import CosmicGovernanceService

# Create existential protocol
protocol = CosmicGovernanceService.create_existential_protocol(
    protocol_name="Universal Ethics",
    description="Core ethical guidelines",
    cosmic_rules={"rule1": "value1"},
    version="1.0.0"
)

# Activate protocol
CosmicGovernanceService.activate_protocol(protocol)

# Create cosmic council
council = CosmicGovernanceService.create_cosmic_council(
    council_name="Ethics Council",
    council_purpose="Oversee ethical protocols",
    founding_members=["consciousness-1", "consciousness-2", "consciousness-3"]
)

# Propose decision
decision_id = CosmicGovernanceService.propose_council_decision(
    council=council,
    decision_title="New Ethics Rule",
    decision_description="Add new ethical guideline",
    proposed_by="consciousness-1"
)

# Vote on decision
CosmicGovernanceService.vote_on_decision(
    council=council,
    decision_id=decision_id,
    voter_signature="consciousness-2",
    vote=True,
    reasoning="Aligns with core values"
)
```

### Advanced Usage (Direct Component Access)

```python
from app.services.governance.application import (
    ProtocolManager,
    CouncilManager,
    TransparencyService,
)
from app.services.governance.infrastructure import (
    SQLAlchemyProtocolRepository,
    SQLAlchemyCouncilRepository,
    SQLAlchemyTransparencyRepository,
)

# Create repositories
protocol_repo = SQLAlchemyProtocolRepository()
council_repo = SQLAlchemyCouncilRepository()
transparency_repo = SQLAlchemyTransparencyRepository()

# Create managers
protocol_mgr = ProtocolManager(protocol_repo, transparency_repo)
council_mgr = CouncilManager(council_repo, transparency_repo)

# Use managers directly
protocol = protocol_mgr.create_protocol(
    name="Test Protocol",
    description="Test",
    rules={}
)
```

## Features

### Existential Protocols
- Self-enforcing opt-in policies
- Version management
- Compliance checking
- Auto-realignment

### Cosmic Governance Councils
- Multi-member councils
- Consensus-based decisions
- Voting mechanisms
- Analytics

### Consciousness Management
- Consciousness signatures
- Understanding levels
- Consensus algorithms
- Auto-realignment

### Existential Transparency
- Complete audit trail
- Event logging
- Query capabilities
- Impact tracking

## Benefits

### Before (Monolithic)
- ❌ 714 lines in single file
- ❌ 6+ responsibilities mixed together
- ❌ Difficult to test
- ❌ Hard to maintain
- ❌ Tight coupling

### After (Hexagonal)
- ✅ 12 specialized files
- ✅ Single Responsibility Principle
- ✅ Easy to test each component
- ✅ Easy to maintain and extend
- ✅ Loose coupling via ports
- ✅ 100% backward compatible

## Testing

Run tests:
```bash
python -m pytest tests/services/governance/
```

## Migration Guide

No migration needed! The facade maintains 100% backward compatibility with the original API.

### Old Code (Still Works)
```python
from app.services.cosmic_governance_service import CosmicGovernanceService

protocol = CosmicGovernanceService.create_existential_protocol(...)
```

### New Code (Recommended)
```python
from app.services.governance import CosmicGovernanceService

protocol = CosmicGovernanceService.create_existential_protocol(...)
```

## Future Enhancements

### Planned
- Blockchain-based transparency
- Distributed consensus protocols
- AI-powered compliance checking
- Real-time governance dashboards
- Multi-dimensional voting

### Easy to Add
Thanks to Hexagonal Architecture, new features can be added by:
1. Creating new application services
2. Implementing new infrastructure adapters
3. No changes to domain layer
4. Backward compatibility maintained

## Principles Applied

- **Single Responsibility Principle**: Each class has one reason to change
- **Dependency Inversion**: Depend on abstractions (ports), not concretions
- **Hexagonal Architecture**: Domain at center, infrastructure at edges
- **Ports & Adapters**: Clear boundaries between layers
- **Open/Closed**: Open for extension, closed for modification

---

**Built with ❤️ by Houssam Benmerah**

*Applying Clean Architecture & SOLID Principles*
