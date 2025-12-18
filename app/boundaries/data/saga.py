"""Data Boundary Saga - Distributed transaction coordination."""
from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class SagaStepStatus(Enum):
    """حالات خطوة Saga"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    COMPENSATED = 'compensated'


@dataclass
class SagaStep:
    """
    خطوة في Saga

    كل خطوة تحتوي على:
    - action: العملية الأساسية
    - compensation: العملية التعويضية (للرجوع عند الفشل)
    """
    step_id: str
    step_name: str
    action: Callable[..., Awaitable[Any]]
    compensation: Callable[..., Awaitable[Any]]
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SagaOrchestrator:
    """
    منسق Saga (Saga Orchestrator)

    يدير تنفيذ Saga مع معاملات التعويض عند الفشل:
    1. تنفيذ الخطوات بالترتيب
    2. عند فشل خطوة، تنفيذ التعويضات بالعكس
    3. ضمان التناسق النهائي

    مثال: إنشاء طلب
    1. إنشاء طلب (PENDING) → نجح → OrderCreated
    2. حجز المخزون → نجح → InventoryReserved
    3. معالجة الدفع → فشل → تعويض: ReleaseInventory + CancelOrder
    """

    def __init__(self, saga_name: str):
        self.saga_name = saga_name
        self.steps: list[SagaStep] = []
        self.current_step_index = 0
        self.saga_id = str(uuid.uuid4())
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

    def add_step(self, step_name: str, action: Callable[..., Awaitable[Any]],
                 compensation: Callable[..., Awaitable[Any]]) -> None:
        """إضافة خطوة جديدة إلى Saga"""
        step_id = f'{self.saga_id}:{len(self.steps)}'
        step = SagaStep(step_id=step_id, step_name=step_name, action=action,
            compensation=compensation)
        self.steps.append(step)
        logger.info(f'➕ Added step {step_name} to saga {self.saga_name}')

    async def execute(self) -> bool:
        """
        تنفيذ Saga

        Returns:
            True إذا نجحت جميع الخطوات، False إذا حدث فشل
        """
        self.started_at = datetime.now()
        logger.info(f'🚀 Starting saga {self.saga_name} ({self.saga_id})')
        for i, step in enumerate(self.steps):
            self.current_step_index = i
            step.status = SagaStepStatus.RUNNING
            step.started_at = datetime.now()
            try:
                logger.info(f'▶️ Executing step {i + 1}/{len(self.steps)}: {step.step_name}')
                step.result = await step.action()
                step.status = SagaStepStatus.COMPLETED
                step.completed_at = datetime.now()
                logger.info(f'✅ Step {step.step_name} completed')
            except Exception as e:
                step.status = SagaStepStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.now()
                logger.error(f'❌ Step {step.step_name} failed: {e}')
                await self._compensate(i)
                return False
        self.completed_at = datetime.now()
        logger.info(f'✅ Saga {self.saga_name} completed successfully')
        return True

    async def _compensate(self, failed_step_index: int) -> None:
        """
        تنفيذ معاملات التعويض (Compensating Transactions)

        Args:
            failed_step_index: فهرس الخطوة التي فشلت
        """
        logger.warning(f'🔄 Starting compensation for saga {self.saga_name}')
        for i in range(failed_step_index - 1, -1, -1):
            step = self.steps[i]
            if step.status == SagaStepStatus.COMPLETED:
                try:
                    logger.info(f'↩️ Compensating step: {step.step_name}')
                    await step.compensation()
                    step.status = SagaStepStatus.COMPENSATED
                    logger.info(f'✅ Compensated step: {step.step_name}')
                except Exception as e:
                    logger.error(f'❌ Failed to compensate step {step.step_name}: {e}')
