"""
Ensemble Router
===============
Routes requests to multiple models and aggregates their responses.
"""
from __future__ import annotations

import threading
import uuid
from collections import Counter
from typing import Any

from app.services.serving.domain.entities import EnsembleConfig, ModelResponse


class EnsembleRouter:
    """
    Ensemble Router - موجه التجميع

    Responsibilities:
    - Create and manage ensemble configurations
    - Route requests to multiple models
    - Aggregate responses using different strategies (voting, averaging, etc.)
    """

    def __init__(self):
        self._ensembles: dict[str, EnsembleConfig] = {}
        self._lock = threading.RLock()

    def create_ensemble(self, model_versions: list[str], aggregation_method:
        str='voting', weights: (dict[str, float] | None)=None) ->str:
        """
        إنشاء تجميع نماذج (Ensemble)

        Args:
            model_versions: قائمة معرفات النماذج
            aggregation_method: طريقة الدمج (voting, averaging, stacking)
            weights: أوزان النماذج (اختياري)

        Returns:
            معرف التجميع
        """
        ensemble_id = str(uuid.uuid4())
        config = EnsembleConfig(ensemble_id=ensemble_id, model_versions=
            model_versions, aggregation_method=aggregation_method, weights=
            weights or {})
        with self._lock:
            self._ensembles[ensemble_id] = config
        return ensemble_id

    def _voting_aggregation(self, responses: list[ModelResponse]) ->Any:
        """التصويت الأغلبي"""
        results = [r.output_data for r in responses if r.success]
        if not results:
            return None
        result_counts = Counter(str(r) for r in results)
        most_common = result_counts.most_common(1)[0][0]
        return most_common

    def _averaging_aggregation(self, responses: list[ModelResponse]) ->dict[
        str, Any]:
        """المتوسط (للقيم الرقمية)"""
        results = [r.output_data for r in responses if r.success]
        return {'averaged_results': results}

    def _default_aggregation(self, responses: list[ModelResponse]) ->dict[
        str, Any]:
        """الافتراضي: إرجاع جميع النتائج"""
        return {'ensemble_results': [r.output_data for r in responses],
            'individual_latencies': [r.latency_ms for r in responses]}

    def create_ensemble_response(self, ensemble_id: str, aggregated_output:
        Any, responses: list[ModelResponse], total_latency: float
        ) ->ModelResponse:
        """
        إنشاء استجابة التجميع

        Args:
            ensemble_id: معرف التجميع
            aggregated_output: النتيجة المدمجة
            responses: قائمة استجابات النماذج الفردية
            total_latency: إجمالي وقت الاستجابة

        Returns:
            استجابة التجميع
        """
        request_id = str(uuid.uuid4())
        return ModelResponse(request_id=request_id, model_id=
            f'ensemble-{ensemble_id}', version_id=ensemble_id, output_data=
            aggregated_output, latency_ms=total_latency, tokens_used=sum(r.
            tokens_used for r in responses), cost_usd=sum(r.cost_usd for r in
            responses), success=all(r.success for r in responses))
