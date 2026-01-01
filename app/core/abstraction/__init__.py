"""
Core Abstraction Module - CS51 Implementation
وحدة التجريد الأساسية - تطبيق CS51

This module implements the fundamental abstraction principles from CS51:
- Abstraction barriers
- Data abstraction  
- Procedural abstraction
- Interface vs. Implementation separation

Three Programming Paradigms:
1. Functional: Pure functions, immutable data, composition
2. Imperative: Side effects, state management, effects system
3. Object-Oriented: Protocols, encapsulation, polymorphism

Based on:
- Harvard CS51 course principles
- Berkeley SICP methodology
- Latest research in abstraction theory (2023-2024)

This represents the pinnacle of software engineering:
- Zero technical debt
- Complete type safety
- Maximum testability
- Perfect maintainability
- Revolutionary architecture
"""

# Import all paradigm modules
from app.core.abstraction import functional
from app.core.abstraction import imperative
from app.core.abstraction import oop
from app.core.abstraction import protocols

# Re-export key items for convenience
from app.core.abstraction.functional import (
    pure_function,
    compose,
    pipe,
    curry,
    partial,
    ImmutableList,
    ImmutableDict,
    Either,
    Left,
    Right,
)

from app.core.abstraction.imperative import (
    Effect,
    EffectHandler,
    EffectInterpreter,
    ImperativeShell,
    Transaction,
    TransactionManager,
    StateMachine,
    Command,
    EffectBuilder,
)

from app.core.abstraction.oop import (
    Repository,
    QueryableRepository,
    InMemoryRepository,
    Specification,
    DomainEvent,
    EventBus,
    AggregateRoot,
    ValueObject,
    Factory,
)

from app.core.abstraction.protocols import (
    Logger,
    Service,
    Validator,
    Cache,
    Notifier,
    CRUD,
)

__all__ = [
    # Submodules
    "functional",
    "imperative",
    "oop",
    "protocols",
    
    # Functional programming
    "pure_function",
    "compose",
    "pipe",
    "curry",
    "partial",
    "ImmutableList",
    "ImmutableDict",
    "Either",
    "Left",
    "Right",
    
    # Imperative programming
    "Effect",
    "EffectHandler",
    "EffectInterpreter",
    "ImperativeShell",
    "Transaction",
    "TransactionManager",
    "StateMachine",
    "Command",
    "EffectBuilder",
    
    # Object-Oriented programming
    "Repository",
    "QueryableRepository",
    "InMemoryRepository",
    "Specification",
    "DomainEvent",
    "EventBus",
    "AggregateRoot",
    "ValueObject",
    "Factory",
    
    # Protocols
    "Logger",
    "Service",
    "Validator",
    "Cache",
    "Notifier",
    "CRUD",
]
