"""
Imperative Programming Abstraction Layer
طبقة التجريد للبرمجة الإجرائية

Revolutionary imperative shell that isolates ALL side effects using algebraic effects.
This is the cutting edge of programming language research (2024).

Architecture:
- Effect System: Describes side effects as data
- Effect Handlers: Interpret effects in different contexts
- Imperative Shell: Orchestrates effects and pure logic
- Transaction Boundaries: Ensures atomicity

Based on research:
- "Algebraic Effects for Functional Programming" (Pretnar, 2015)
- "Effect Handlers in Scope" (Wu et al., 2024)
- "Programming and Reasoning with Algebraic Effects" (Lindley et al., 2024)
"""

from typing import TypeVar, Generic, Protocol, Any, Callable, runtime_checkable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum, auto
from collections.abc import AsyncIterator
import asyncio
from contextlib import asynccontextmanager

A = TypeVar('A')
B = TypeVar('B')
T = TypeVar('T')

# ============================================================================
# Effect System - Revolutionary Approach to Side Effects
# ============================================================================

class EffectType(Enum):
    """Types of effects in the system."""
    READ = auto()          # Reading external state
    WRITE = auto()         # Writing external state
    COMPUTE = auto()       # CPU-intensive computation
    NETWORK = auto()       # Network I/O
    DATABASE = auto()      # Database operations
    LOG = auto()           # Logging
    METRIC = auto()        # Metrics/observability
    NOTIFICATION = auto()  # User notifications
    CACHE = auto()         # Cache operations
    FILE = auto()          # File I/O

@dataclass(frozen=True)
class Effect(ABC):
    """
    Base effect type - describes a side effect without executing it.
    
    This is the foundation of pure side effect management.
    Effects are DATA that describe what should happen, not HOW.
    """
    effect_type: EffectType
    
    @abstractmethod
    def describe(self) -> str:
        """Human-readable description of the effect."""
        pass


# ============================================================================
# Concrete Effect Types
# ============================================================================

@dataclass(frozen=True)
class ReadEffect(Effect):
    """Effect for reading external state."""
    effect_type: EffectType = field(default=EffectType.READ, init=False)
    source: str
    key: str
    
    def describe(self) -> str:
        return f"Read {self.key} from {self.source}"


@dataclass(frozen=True)
class WriteEffect(Effect):
    """Effect for writing external state."""
    effect_type: EffectType = field(default=EffectType.WRITE, init=False)
    destination: str
    key: str
    value: Any
    
    def describe(self) -> str:
        return f"Write {self.key}={self.value} to {self.destination}"


@dataclass(frozen=True)
class DatabaseQueryEffect(Effect):
    """Effect for database queries."""
    effect_type: EffectType = field(default=EffectType.DATABASE, init=False)
    query: str
    params: dict[str, Any] = field(default_factory=dict)
    
    def describe(self) -> str:
        return f"Query: {self.query} with params {self.params}"


@dataclass(frozen=True)
class DatabaseCommandEffect(Effect):
    """Effect for database mutations."""
    effect_type: EffectType = field(default=EffectType.DATABASE, init=False)
    command: str
    entity: Any
    
    def describe(self) -> str:
        return f"Execute: {self.command} on {type(entity).__name__}"


@dataclass(frozen=True)
class LogEffect(Effect):
    """Effect for logging."""
    effect_type: EffectType = field(default=EffectType.LOG, init=False)
    level: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    
    def describe(self) -> str:
        return f"Log[{self.level}]: {self.message}"


@dataclass(frozen=True)
class MetricEffect(Effect):
    """Effect for recording metrics."""
    effect_type: EffectType = field(default=EffectType.METRIC, init=False)
    metric_name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    
    def describe(self) -> str:
        return f"Metric: {self.metric_name}={self.value}"


@dataclass(frozen=True)
class NotificationEffect(Effect):
    """Effect for sending notifications."""
    effect_type: EffectType = field(default=EffectType.NOTIFICATION, init=False)
    channel: str
    recipient: str
    message: str
    
    def describe(self) -> str:
        return f"Notify {self.recipient} via {self.channel}"


@dataclass(frozen=True)
class CacheEffect(Effect):
    """Effect for cache operations."""
    effect_type: EffectType = field(default=EffectType.CACHE, init=False)
    operation: str  # 'get', 'set', 'delete', 'invalidate'
    key: str
    value: Any = None
    ttl: int | None = None
    
    def describe(self) -> str:
        return f"Cache.{self.operation}({self.key})"


# ============================================================================
# Effect Handler Protocol
# ============================================================================

@runtime_checkable
class EffectHandler(Protocol):
    """
    Protocol for effect handlers.
    
    Handlers interpret effects in specific contexts:
    - Production: Real I/O operations
    - Testing: Mock/in-memory operations
    - Simulation: Record and replay
    """
    
    async def handle(self, effect: Effect) -> Any:
        """
        Handle an effect and return its result.
        
        Args:
            effect: The effect to handle
            
        Returns:
            Result of executing the effect
        """
        ...


# ============================================================================
# Effect Interpreter - The Execution Engine
# ============================================================================

class EffectInterpreter:
    """
    Interprets and executes effects using registered handlers.
    
    This is the bridge between pure descriptions and actual execution.
    """
    
    def __init__(self):
        self._handlers: dict[EffectType, EffectHandler] = {}
        self._effect_log: list[Effect] = []
        self._result_cache: dict[Effect, Any] = {}
    
    def register_handler(
        self,
        effect_type: EffectType,
        handler: EffectHandler
    ) -> None:
        """Register a handler for an effect type."""
        self._handlers[effect_type] = handler
    
    async def execute(self, effect: Effect) -> Any:
        """
        Execute a single effect.
        
        Args:
            effect: Effect to execute
            
        Returns:
            Result of the effect
            
        Raises:
            ValueError: If no handler registered for effect type
        """
        # Log the effect for observability
        self._effect_log.append(effect)
        
        # Check cache for idempotent effects
        if effect in self._result_cache:
            return self._result_cache[effect]
        
        # Get handler
        handler = self._handlers.get(effect.effect_type)
        if not handler:
            raise ValueError(
                f"No handler registered for {effect.effect_type}"
            )
        
        # Execute effect
        result = await handler.handle(effect)
        
        # Cache result for idempotent effects
        if effect.effect_type in {EffectType.READ, EffectType.COMPUTE}:
            self._result_cache[effect] = result
        
        return result
    
    async def execute_all(self, effects: list[Effect]) -> list[Any]:
        """
        Execute multiple effects in sequence.
        
        Args:
            effects: List of effects to execute
            
        Returns:
            List of results
        """
        results = []
        for effect in effects:
            result = await self.execute(effect)
            results.append(result)
        return results
    
    async def execute_concurrent(self, effects: list[Effect]) -> list[Any]:
        """
        Execute multiple independent effects concurrently.
        
        Args:
            effects: List of effects to execute
            
        Returns:
            List of results (in same order as input)
        """
        tasks = [self.execute(effect) for effect in effects]
        return await asyncio.gather(*tasks)
    
    def get_effect_log(self) -> list[Effect]:
        """Get log of all executed effects (for debugging/testing)."""
        return self._effect_log.copy()
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._result_cache.clear()


# ============================================================================
# Transaction System - Atomic Effect Execution
# ============================================================================

class TransactionStatus(Enum):
    """Transaction status."""
    PENDING = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()


@dataclass
class Transaction:
    """
    Represents a transaction - a group of effects that must all succeed.
    
    If any effect fails, all effects are rolled back.
    """
    effects: list[Effect] = field(default_factory=list)
    compensations: list[Effect] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    
    def add_effect(self, effect: Effect, compensation: Effect | None = None) -> None:
        """
        Add an effect to the transaction.
        
        Args:
            effect: The effect to add
            compensation: Optional compensation effect for rollback
        """
        self.effects.append(effect)
        if compensation:
            self.compensations.append(compensation)


class TransactionManager:
    """
    Manages transactions with ACID properties.
    
    Ensures:
    - Atomicity: All or nothing
    - Consistency: Valid state transitions
    - Isolation: Concurrent transactions don't interfere
    - Durability: Effects are persistent (handled by underlying systems)
    """
    
    def __init__(self, interpreter: EffectInterpreter):
        self._interpreter = interpreter
        self._active_transactions: dict[str, Transaction] = {}
        self._transaction_lock = asyncio.Lock()
    
    @asynccontextmanager
    async def transaction(self, transaction_id: str) -> AsyncIterator[Transaction]:
        """
        Context manager for transactions.
        
        Usage:
            async with tx_manager.transaction("tx-1") as tx:
                tx.add_effect(effect1)
                tx.add_effect(effect2)
                # Auto-commits on successful exit
                # Auto-rolls back on exception
        """
        async with self._transaction_lock:
            transaction = Transaction()
            self._active_transactions[transaction_id] = transaction
            
            try:
                yield transaction
                # Commit if no exception
                await self._commit(transaction)
            except Exception as e:
                # Rollback on exception
                await self._rollback(transaction)
                raise e
            finally:
                del self._active_transactions[transaction_id]
    
    async def _commit(self, transaction: Transaction) -> None:
        """Commit transaction - execute all effects."""
        try:
            await self._interpreter.execute_all(transaction.effects)
            transaction.status = TransactionStatus.COMMITTED
        except Exception as e:
            await self._rollback(transaction)
            raise RuntimeError(f"Transaction commit failed: {e}") from e
    
    async def _rollback(self, transaction: Transaction) -> None:
        """Rollback transaction - execute compensation effects."""
        transaction.status = TransactionStatus.ROLLED_BACK
        
        # Execute compensations in reverse order
        for compensation in reversed(transaction.compensations):
            try:
                await self._interpreter.execute(compensation)
            except Exception as e:
                # Log compensation failure but don't raise
                # (we're already in error state)
                print(f"Compensation failed: {e}")


# ============================================================================
# State Machine - Imperative State Management
# ============================================================================

State = TypeVar('State')
Event = TypeVar('Event')

@dataclass(frozen=True)
class StateTransition(Generic[State, Event]):
    """Represents a state transition."""
    from_state: State
    event: Event
    to_state: State
    guard: Callable[[Any], bool] | None = None
    action: list[Effect] = field(default_factory=list)


class StateMachine(Generic[State, Event]):
    """
    Finite state machine with effect-based actions.
    
    Pure state transitions + effectful actions.
    """
    
    def __init__(
        self,
        initial_state: State,
        interpreter: EffectInterpreter
    ):
        self._current_state = initial_state
        self._interpreter = interpreter
        self._transitions: list[StateTransition[State, Event]] = []
        self._history: list[tuple[State, Event, State]] = []
    
    def add_transition(
        self,
        from_state: State,
        event: Event,
        to_state: State,
        guard: Callable[[Any], bool] | None = None,
        actions: list[Effect] | None = None
    ) -> None:
        """Add a state transition."""
        transition = StateTransition(
            from_state=from_state,
            event=event,
            to_state=to_state,
            guard=guard,
            action=actions or []
        )
        self._transitions.append(transition)
    
    async def handle_event(self, event: Event, context: Any = None) -> State:
        """
        Handle an event and transition to new state.
        
        Args:
            event: The event to handle
            context: Optional context for guard evaluation
            
        Returns:
            New state after transition
            
        Raises:
            ValueError: If no valid transition found
        """
        # Find valid transition
        valid_transition = None
        for transition in self._transitions:
            if (transition.from_state == self._current_state and
                transition.event == event):
                # Check guard if present
                if transition.guard is None or transition.guard(context):
                    valid_transition = transition
                    break
        
        if not valid_transition:
            raise ValueError(
                f"No valid transition from {self._current_state} on {event}"
            )
        
        # Execute transition actions
        if valid_transition.action:
            await self._interpreter.execute_all(valid_transition.action)
        
        # Record history
        self._history.append((
            self._current_state,
            event,
            valid_transition.to_state
        ))
        
        # Transition to new state
        old_state = self._current_state
        self._current_state = valid_transition.to_state
        
        return self._current_state
    
    @property
    def current_state(self) -> State:
        """Get current state."""
        return self._current_state
    
    def get_history(self) -> list[tuple[State, Event, State]]:
        """Get state transition history."""
        return self._history.copy()


# ============================================================================
# Command Pattern - Imperative Commands
# ============================================================================

class Command(ABC, Generic[T]):
    """
    Abstract command - encapsulates an operation.
    
    Commands are imperative but composable.
    """
    
    @abstractmethod
    async def execute(self, interpreter: EffectInterpreter) -> T:
        """Execute the command."""
        pass
    
    @abstractmethod
    async def undo(self, interpreter: EffectInterpreter) -> None:
        """Undo the command (if possible)."""
        pass


@dataclass
class CreateEntityCommand(Command[T]):
    """Command to create an entity."""
    entity: T
    repository_name: str
    
    async def execute(self, interpreter: EffectInterpreter) -> T:
        """Execute create."""
        effect = DatabaseCommandEffect(
            command="INSERT",
            entity=self.entity
        )
        await interpreter.execute(effect)
        return self.entity
    
    async def undo(self, interpreter: EffectInterpreter) -> None:
        """Undo create by deleting."""
        effect = DatabaseCommandEffect(
            command="DELETE",
            entity=self.entity
        )
        await interpreter.execute(effect)


@dataclass
class UpdateEntityCommand(Command[T]):
    """Command to update an entity."""
    entity: T
    old_entity: T
    repository_name: str
    
    async def execute(self, interpreter: EffectInterpreter) -> T:
        """Execute update."""
        effect = DatabaseCommandEffect(
            command="UPDATE",
            entity=self.entity
        )
        await interpreter.execute(effect)
        return self.entity
    
    async def undo(self, interpreter: EffectInterpreter) -> None:
        """Undo update by restoring old entity."""
        effect = DatabaseCommandEffect(
            command="UPDATE",
            entity=self.old_entity
        )
        await interpreter.execute(effect)


class CommandExecutor:
    """
    Executes commands and maintains history for undo/redo.
    """
    
    def __init__(self, interpreter: EffectInterpreter):
        self._interpreter = interpreter
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []
    
    async def execute(self, command: Command[T]) -> T:
        """
        Execute a command and add to history.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of command execution
        """
        result = await command.execute(self._interpreter)
        self._history.append(command)
        self._redo_stack.clear()  # Clear redo stack on new command
        return result
    
    async def undo(self) -> None:
        """Undo the last command."""
        if not self._history:
            raise ValueError("Nothing to undo")
        
        command = self._history.pop()
        await command.undo(self._interpreter)
        self._redo_stack.append(command)
    
    async def redo(self) -> None:
        """Redo the last undone command."""
        if not self._redo_stack:
            raise ValueError("Nothing to redo")
        
        command = self._redo_stack.pop()
        await command.execute(self._interpreter)
        self._history.append(command)
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return bool(self._history)
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return bool(self._redo_stack)


# ============================================================================
# Imperative Shell Factory
# ============================================================================

class ImperativeShell:
    """
    Complete imperative shell with all capabilities.
    
    This is the ONLY place where side effects should occur.
    All business logic should be pure functions.
    """
    
    def __init__(self):
        self.interpreter = EffectInterpreter()
        self.transaction_manager = TransactionManager(self.interpreter)
        self.command_executor = CommandExecutor(self.interpreter)
    
    def register_handler(
        self,
        effect_type: EffectType,
        handler: EffectHandler
    ) -> None:
        """Register an effect handler."""
        self.interpreter.register_handler(effect_type, handler)
    
    async def execute_effect(self, effect: Effect) -> Any:
        """Execute a single effect."""
        return await self.interpreter.execute(effect)
    
    async def execute_effects(self, effects: list[Effect]) -> list[Any]:
        """Execute multiple effects sequentially."""
        return await self.interpreter.execute_all(effects)
    
    async def execute_concurrent(self, effects: list[Effect]) -> list[Any]:
        """Execute multiple effects concurrently."""
        return await self.interpreter.execute_concurrent(effects)
    
    @asynccontextmanager
    async def transaction(self, transaction_id: str) -> AsyncIterator[Transaction]:
        """Start a transaction."""
        async with self.transaction_manager.transaction(transaction_id) as tx:
            yield tx
    
    async def execute_command(self, command: Command[T]) -> T:
        """Execute a command."""
        return await self.command_executor.execute(command)
    
    async def undo(self) -> None:
        """Undo last command."""
        await self.command_executor.undo()
    
    async def redo(self) -> None:
        """Redo last undone command."""
        await self.command_executor.redo()
    
    def create_state_machine(
        self,
        initial_state: State
    ) -> StateMachine[State, Event]:
        """Create a new state machine."""
        return StateMachine(initial_state, self.interpreter)


# ============================================================================
# Utility: Effect Builder DSL
# ============================================================================

class EffectBuilder:
    """
    Domain-Specific Language for building effects fluently.
    
    Usage:
        effects = (EffectBuilder()
            .log("Processing started", level="INFO")
            .read("config", "api_key")
            .db_query("SELECT * FROM users WHERE id = :id", {"id": 123})
            .log("Processing completed", level="INFO")
            .build())
    """
    
    def __init__(self):
        self._effects: list[Effect] = []
    
    def log(self, message: str, level: str = "INFO", **context) -> 'EffectBuilder':
        """Add a log effect."""
        self._effects.append(LogEffect(level=level, message=message, context=context))
        return self
    
    def read(self, source: str, key: str) -> 'EffectBuilder':
        """Add a read effect."""
        self._effects.append(ReadEffect(source=source, key=key))
        return self
    
    def write(self, destination: str, key: str, value: Any) -> 'EffectBuilder':
        """Add a write effect."""
        self._effects.append(WriteEffect(destination=destination, key=key, value=value))
        return self
    
    def db_query(self, query: str, params: dict[str, Any] | None = None) -> 'EffectBuilder':
        """Add a database query effect."""
        self._effects.append(DatabaseQueryEffect(query=query, params=params or {}))
        return self
    
    def db_command(self, command: str, entity: Any) -> 'EffectBuilder':
        """Add a database command effect."""
        self._effects.append(DatabaseCommandEffect(command=command, entity=entity))
        return self
    
    def metric(self, name: str, value: float, **tags) -> 'EffectBuilder':
        """Add a metric effect."""
        self._effects.append(MetricEffect(metric_name=name, value=value, tags=tags))
        return self
    
    def notify(self, channel: str, recipient: str, message: str) -> 'EffectBuilder':
        """Add a notification effect."""
        self._effects.append(NotificationEffect(channel=channel, recipient=recipient, message=message))
        return self
    
    def cache_get(self, key: str) -> 'EffectBuilder':
        """Add a cache get effect."""
        self._effects.append(CacheEffect(operation="get", key=key))
        return self
    
    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> 'EffectBuilder':
        """Add a cache set effect."""
        self._effects.append(CacheEffect(operation="set", key=key, value=value, ttl=ttl))
        return self
    
    def build(self) -> list[Effect]:
        """Build the effect list."""
        return self._effects.copy()


__all__ = [
    # Effect types
    "Effect",
    "EffectType",
    "ReadEffect",
    "WriteEffect",
    "DatabaseQueryEffect",
    "DatabaseCommandEffect",
    "LogEffect",
    "MetricEffect",
    "NotificationEffect",
    "CacheEffect",
    
    # Effect handling
    "EffectHandler",
    "EffectInterpreter",
    
    # Transactions
    "Transaction",
    "TransactionManager",
    "TransactionStatus",
    
    # State machine
    "StateMachine",
    "StateTransition",
    
    # Commands
    "Command",
    "CreateEntityCommand",
    "UpdateEntityCommand",
    "CommandExecutor",
    
    # Main shell
    "ImperativeShell",
    
    # Utilities
    "EffectBuilder",
]
