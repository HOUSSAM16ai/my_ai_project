"""
Model Version Entity
====================
Domain entity representing a version of an AI model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ModelStatus(Enum):
    """حالات النموذج"""

    LOADING = "loading"
    READY = "ready"
    SERVING = "serving"
    DRAINING = "draining"  # يستنزف الطلبات الحالية قبل الإيقاف
    STOPPED = "stopped"
    FAILED = "failed"


class ModelType(Enum):
    """أنواع النماذج"""

    LANGUAGE_MODEL = "language_model"  # نماذج اللغة (GPT, Claude, etc.)
    VISION_MODEL = "vision_model"  # نماذج الرؤية
    EMBEDDING_MODEL = "embedding_model"  # نماذج التضمين
    CUSTOM_MODEL = "custom_model"  # نماذج مخصصة


@dataclass
class ModelVersion:
    """نسخة من النموذج"""

    version_id: str
    model_name: str
    version_number: str
    model_type: ModelType
    status: ModelStatus
    endpoint: str | None = None
    framework: str = "pytorch"  # pytorch, tensorflow, onnx
    device: str = "cpu"  # cpu, cuda, mps
    batch_size: int = 1
    max_sequence_length: int = 2048
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    loaded_at: datetime | None = None
