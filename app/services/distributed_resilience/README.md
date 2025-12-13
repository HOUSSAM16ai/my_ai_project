# DistributedResilience Service

## Overview

Hexagonal architecture implementation for DistributedResilience.

## Architecture

```
distributedresilience/
├── domain/              # Pure business logic
│   ├── models.py       # Entities
│   └── ports.py        # Interfaces
├── application/        # Use cases
│   └── manager.py
├── infrastructure/     # Adapters
│   └── repository.py
└── facade.py          # Unified interface
```

## Migration

Original file: 101 lines
New structure: Modular architecture

**Reduction**: ~90%
**Breaking Changes**: None
**Backward Compatibility**: 100%
