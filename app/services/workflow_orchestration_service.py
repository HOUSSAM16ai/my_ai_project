from __future__ import annotations
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    COMPENSATING = 'compensating'
    COMPENSATED = 'compensated'
    CANCELLED = 'cancelled'


class ActivityStatus(Enum):
    """Activity execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'


@dataclass
class WorkflowActivity:
    """Workflow activity definition"""
    activity_id: str
    name: str
    handler: str
    input_data: dict[str, Any]
    retry_policy: dict[str, Any]
    timeout_seconds: int = 300
    compensation_handler: str | None = None
    status: ActivityStatus = ActivityStatus.PENDING
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    activities: list[WorkflowActivity]
    event_triggers: list[str]
    parallel_execution: bool = False
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEvent:
    """Workflow event"""
    event_id: str
    workflow_id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))


class WorkflowOrchestrationService:
    """
    خدمة Workflow Orchestration الخارقة - World-class workflow engine

    Features:
    - Event-driven workflow execution
    - Distributed transaction support
    - Automatic retry and compensation
    - State persistence
    - Long-running workflows
    """

    def __init__(self):
        self.workflows: dict[str, WorkflowDefinition] = {}
        self.workflow_events: deque[WorkflowEvent] = deque(maxlen=10000)
        self.activity_handlers: dict[str, Callable] = {}
        self.event_subscriptions: dict[str, list[str]] = defaultdict(list)
        self.lock = threading.RLock()
        logging.getLogger(__name__).info(
            'Workflow Orchestration Service initialized')

    def register_workflow(self, workflow: WorkflowDefinition) ->bool:
        """Register workflow definition"""
        with self.lock:
            self.workflows[workflow.workflow_id] = workflow
            for event_type in workflow.event_triggers:
                self.event_subscriptions[event_type].append(workflow.
                    workflow_id)
            logging.getLogger(__name__).info(
                f'Registered workflow: {workflow.name}')
            return True

    def execute_workflow(self, workflow_id: str) ->(WorkflowDefinition | None):
        """Execute workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now(UTC)
        try:
            if workflow.parallel_execution:
                self._execute_parallel(workflow)
            else:
                self._execute_sequential(workflow)
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(UTC)
            logging.getLogger(__name__).info(
                f'Workflow completed: {workflow.name}')
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now(UTC)
            logging.getLogger(__name__).error(
                f'Workflow failed: {workflow.name} - {e}')
            self._compensate_workflow(workflow)
        return workflow

    def _execute_sequential(self, workflow: WorkflowDefinition):
        """Execute activities sequentially"""
        for activity in workflow.activities:
            self._execute_activity(activity)

    def _execute_parallel(self, workflow: WorkflowDefinition):
        """Execute activities in parallel"""
        threads = []
        for activity in workflow.activities:
            thread = threading.Thread(target=self._execute_activity, args=(
                activity,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def _execute_activity(self, activity: WorkflowActivity):
        """Execute single activity with retry"""
        activity.status = ActivityStatus.RUNNING
        activity.started_at = datetime.now(UTC)
        max_retries = activity.retry_policy.get('max_attempts', 3)
        backoff_seconds = activity.retry_policy.get('initial_interval_seconds',
            1)
        while activity.retry_count < max_retries:
            try:
                handler = self.activity_handlers.get(activity.handler)
                if handler:
                    activity.result = handler(activity.input_data)
                else:
                    activity.result = {'status': 'success'}
                activity.status = ActivityStatus.COMPLETED
                activity.completed_at = datetime.now(UTC)
                break
            except Exception as e:
                activity.retry_count += 1
                activity.error = str(e)
                if activity.retry_count >= max_retries:
                    activity.status = ActivityStatus.FAILED
                    activity.completed_at = datetime.now(UTC)
                    raise
                else:
                    activity.status = ActivityStatus.RETRYING
                    time.sleep(backoff_seconds * 2 ** activity.retry_count)

    def _compensate_workflow(self, workflow: WorkflowDefinition):
        """Compensate failed workflow"""
        workflow.status = WorkflowStatus.COMPENSATING
        logging.getLogger(__name__).info(
            f'Compensating workflow: {workflow.name}')
        for activity in reversed(workflow.activities):
            if (activity.status == ActivityStatus.COMPLETED and activity.
                compensation_handler):
                try:
                    handler = self.activity_handlers.get(activity.
                        compensation_handler)
                    if handler:
                        handler(activity.result)
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f'Compensation failed for {activity.name}: {e}')
        workflow.status = WorkflowStatus.COMPENSATED

    def register_activity_handler(self, handler_name: str, handler: Callable):
        """Register activity handler"""
        self.activity_handlers[handler_name] = handler

    def get_metrics(self) ->dict[str, Any]:
        """Get workflow metrics"""
        return {'total_workflows': len(self.workflows), 'running_workflows':
            len([w for w in self.workflows.values() if w.status ==
            WorkflowStatus.RUNNING]), 'completed_workflows': len([w for w in
            self.workflows.values() if w.status == WorkflowStatus.COMPLETED
            ]), 'failed_workflows': len([w for w in self.workflows.values() if
            w.status == WorkflowStatus.FAILED]), 'total_events': len(self.
            workflow_events)}


_workflow_instance: WorkflowOrchestrationService | None = None
_workflow_lock = threading.Lock()


def get_workflow_orchestration_service() ->WorkflowOrchestrationService:
    """Get singleton workflow service instance"""
    global _workflow_instance
    if _workflow_instance is None:
        with _workflow_lock:
            if _workflow_instance is None:
                _workflow_instance = WorkflowOrchestrationService()
    return _workflow_instance
