from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from app.core.docs.asyncapi.models import AsyncAPI30, Operation


class ConsumptionModel(StrEnum):
    """يمثل هذا التعداد نموذج الاستهلاك الدلالي عبر البروتوكولات المختلفة."""

    QUEUE = "queue"
    BROADCAST = "broadcast"


@dataclass(frozen=True)
class ConsumptionConflict:
    """يوضح هذا الكائن وجود تعارض دلالي بين نماذج الاستهلاك في قناة واحدة."""

    channel_id: str
    models: frozenset[ConsumptionModel]


def assert_no_mixed_consumption(asyncapi_doc: AsyncAPI30) -> None:
    """
    يتحقق هذا التابع من عدم خلط نماذج استهلاك متعارضة داخل نفس القناة.

    عند وجود عمليات على نفس القناة بدلالات Queue وBroadcast معاً، يتم
    إطلاق خطأ يوضح القناة المتعارضة.
    """
    conflicts = detect_consumption_conflicts(asyncapi_doc)
    if conflicts:
        conflict_labels = ", ".join(
            f"{conflict.channel_id}({sorted({m.value for m in conflict.models})})"
            for conflict in conflicts
        )
        raise ValueError(
            "تعارض دلالات الاستهلاك في قنوات AsyncAPI: "
            f"{conflict_labels}. "
            "افصل القنوات أو وحّد النموذج الدلالي."
        )


def detect_consumption_conflicts(asyncapi_doc: AsyncAPI30) -> list[ConsumptionConflict]:
    """
    يستخرج هذا التابع التعارضات الدلالية بين العمليات المرتبطة بالقنوات.

    يعتمد الكشف على bindings البروتوكولية لكل عملية.
    """
    channel_models: dict[str, set[ConsumptionModel]] = {}

    for operation_id, operation in (asyncapi_doc.operations or {}).items():
        operation_models = _derive_consumption_models(operation, operation_id)
        if not operation_models:
            continue

        channel_id = _channel_id_from_operation(operation)
        if channel_id is None:
            continue

        channel_models.setdefault(channel_id, set()).update(operation_models)

    return [
        ConsumptionConflict(channel_id=channel_id, models=frozenset(models))
        for channel_id, models in channel_models.items()
        if len(models) > 1
    ]


def _derive_consumption_models(
    operation: Operation,
    operation_id: str,
) -> set[ConsumptionModel]:
    """
    يحدد هذا التابع نموذج الاستهلاك اعتماداً على bindings العملية.

    - وجود kafka.groupId يعني Queue/Consumer Group.
    - وجود ws binding يعني Broadcast.
    """
    bindings = operation.bindings or {}
    models: set[ConsumptionModel] = set()

    explicit_model = _explicit_consumption_model(bindings)
    inferred_models = _infer_models_from_bindings(bindings)

    if explicit_model is None:
        return inferred_models

    if inferred_models and explicit_model not in inferred_models:
        inferred = ", ".join(sorted(model.value for model in inferred_models))
        raise ValueError(
            "تعارض بين نموذج الاستهلاك المصرّح به والدلالات المستنتجة "
            f"في العملية {operation_id}: explicit={explicit_model.value}, "
            f"inferred={inferred}. صحّح bindings أو عدّل التصريح."
        )

    models.add(explicit_model)
    return models


def _explicit_consumption_model(
    bindings: Mapping[str, object],
) -> ConsumptionModel | None:
    """يقرأ هذا التابع النموذج المصرّح به عبر x-consumption-model."""
    explicit = bindings.get("x-consumption-model")
    if isinstance(explicit, str):
        normalized = explicit.strip().lower()
        if normalized == ConsumptionModel.QUEUE.value:
            return ConsumptionModel.QUEUE
        if normalized == ConsumptionModel.BROADCAST.value:
            return ConsumptionModel.BROADCAST
    return None


def _infer_models_from_bindings(
    bindings: Mapping[str, object],
) -> set[ConsumptionModel]:
    """يستنتج هذا التابع النموذج الدلالي من bindings البروتوكولية."""
    models: set[ConsumptionModel] = set()

    kafka_binding = _read_binding(bindings, "kafka")
    if kafka_binding and kafka_binding.get("groupId"):
        models.add(ConsumptionModel.QUEUE)

    ws_binding = _read_binding(bindings, "ws")
    if ws_binding:
        models.add(ConsumptionModel.BROADCAST)

    return models


def _read_binding(
    bindings: Mapping[str, object],
    key: str,
) -> Mapping[str, object] | None:
    """يقرأ هذا التابع binding محدداً ويضمن إرجاع بنية قاموسية آمنة."""
    binding = bindings.get(key)
    if isinstance(binding, Mapping):
        return binding
    if isinstance(binding, BaseModel):
        return binding.model_dump(by_alias=True, exclude_none=True)
    return None


def _channel_id_from_operation(operation: Operation) -> str | None:
    """يستخرج هذا التابع معرف القناة من مرجع العملية."""
    ref = operation.channel.ref
    prefix = "#/components/channels/"
    if ref.startswith(prefix):
        return ref[len(prefix) :]
    return None
