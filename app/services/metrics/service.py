import hashlib
import math
import statistics
import threading
import time
import itertools
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.metrics.types import (
    MetricType,
    ModelType,
    DriftStatus,
    InferenceMetrics,
    AccuracyMetrics,
    NLPMetrics,
    LatencyMetrics,
    CostMetrics,
    ModelDriftMetrics,
    FairnessMetrics,
    ModelPerformanceSnapshot,
)
from app.core.utils.text import get_ngrams, get_lcs_length
from app.services.metrics.calculators.drift import DriftCalculatorContext


class AIModelMetricsService:
    """
    خدمة قياس نماذج الذكاء الاصطناعي الخارقة
    World-class AI Model Metrics Service

    Tracks all AI model performance metrics in real-time with advanced
    analytics, drift detection, and fairness monitoring.
    """

    def __init__(self):
        """Initialize AI model metrics service"""
        self.lock = threading.RLock()

        # Model tracking
        self.models: dict[str, dict] = {}  # model_name -> tracking data
        self.inference_buffer: deque = deque(maxlen=10000)
        self.latency_buffer: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Prediction tracking for drift detection
        self.baseline_predictions: dict[str, list] = defaultdict(list)
        self.current_predictions: dict[str, list] = defaultdict(list)

        # Drift Calculator Context
        self.drift_calculator = DriftCalculatorContext()

        # A/B testing support
        self.ab_tests: dict[str, dict] = {}

    def register_model(
        self,
        model_name: str,
        model_version: str,
        model_type: ModelType,
        metadata: dict[str, Any] | None = None,
    ):
        """Register a model for tracking"""
        with self.lock:
            model_key = f"{model_name}:{model_version}"
            if model_key not in self.models:
                self.models[model_key] = {
                    "model_name": model_name,
                    "model_version": model_version,
                    "model_type": model_type,
                    "registered_at": datetime.now(UTC),
                    "metadata": metadata or {},
                    "inference_count": 0,
                    "error_count": 0,
                    "total_latency_ms": 0.0,
                    "total_cost_usd": 0.0,
                }

    def record_inference(
        self,
        model_name: str,
        model_version: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        prediction: Any = None,
        ground_truth: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record a single inference"""
        inference_id = hashlib.sha256(
            f"{model_name}{model_version}{time.time_ns()}".encode()
        ).hexdigest()[:16]

        inference = InferenceMetrics(
            inference_id=inference_id,
            model_name=model_name,
            model_version=model_version,
            timestamp=datetime.now(UTC),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            prediction=prediction,
            ground_truth=ground_truth,
            metadata=metadata or {},
        )

        with self.lock:
            self.inference_buffer.append(inference)

            model_key = f"{model_name}:{model_version}"
            self.latency_buffer[model_key].append(latency_ms)

            if model_key in self.models:
                model = self.models[model_key]
                model["inference_count"] += 1
                model["total_latency_ms"] += latency_ms
                model["total_cost_usd"] += cost_usd

            # Track predictions for drift detection
            if prediction is not None:
                self.current_predictions[model_key].append(prediction)
                if len(self.current_predictions[model_key]) > 1000:
                    self.current_predictions[model_key].pop(0)

        return inference_id

    def calculate_accuracy_metrics(
        self,
        predictions: list[Any],
        ground_truths: list[Any],
        positive_class: Any = 1,
    ) -> AccuracyMetrics:
        """
        Calculate accuracy metrics for classification
        """
        if len(predictions) != len(ground_truths):
            raise ValueError("Predictions and ground truths must have same length")

        tp = fp = tn = fn = 0

        for pred, truth in zip(predictions, ground_truths, strict=False):
            if pred == positive_class and truth == positive_class:
                tp += 1
            elif pred == positive_class and truth != positive_class:
                fp += 1
            elif pred != positive_class and truth != positive_class:
                tn += 1
            else:
                fn += 1

        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return AccuracyMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            sample_count=total,
        )

    def calculate_bleu_score(self, reference: str, candidate: str, max_n: int = 4) -> float:
        """
        Calculate BLEU score for translation/generation quality
        """
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()

        if not cand_tokens:
            return 0.0

        # Calculate n-gram precisions
        precisions = []
        for n in range(1, max_n + 1):
            ref_ngrams = get_ngrams(ref_tokens, n)
            cand_ngrams = get_ngrams(cand_tokens, n)

            matches = sum((ref_ngrams & cand_ngrams).values())
            total = sum(cand_ngrams.values())

            precision = matches / total if total > 0 else 0.0
            precisions.append(precision)

        # Geometric mean of precisions
        if all(p > 0 for p in precisions):
            bleu = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        else:
            bleu = 0.0

        # Brevity penalty
        bp = min(1.0, math.exp(1 - len(ref_tokens) / len(cand_tokens)))

        return bp * bleu

    def calculate_rouge_scores(self, reference: str, candidate: str) -> dict[str, float]:
        """
        Calculate ROUGE scores (simplified version)
        """
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()

        # ROUGE-1 (unigram overlap)
        ref_unigrams = set(ref_tokens)
        cand_unigrams = set(cand_tokens)
        overlapping = len(ref_unigrams & cand_unigrams)
        rouge_1 = overlapping / len(ref_unigrams) if ref_unigrams else 0.0

        # ROUGE-2 (bigram overlap)
        ref_bigrams = set(itertools.pairwise(ref_tokens))
        cand_bigrams = set(itertools.pairwise(cand_tokens))
        overlapping = len(ref_bigrams & cand_bigrams)
        rouge_2 = overlapping / len(ref_bigrams) if ref_bigrams else 0.0

        # ROUGE-L (longest common subsequence)
        lcs_length = get_lcs_length(ref_tokens, cand_tokens)
        rouge_l = lcs_length / len(ref_tokens) if ref_tokens else 0.0

        return {"rouge_1": rouge_1, "rouge_2": rouge_2, "rouge_l": rouge_l}

    def calculate_perplexity(
        self, model_name: str, model_version: str, log_probabilities: list[float]
    ) -> float:
        """
        Calculate perplexity from log probabilities
        """
        if not log_probabilities:
            return float("inf")

        avg_log_prob = sum(log_probabilities) / len(log_probabilities)
        perplexity = math.exp(-avg_log_prob)

        return perplexity

    def get_latency_metrics(self, model_name: str, model_version: str) -> LatencyMetrics | None:
        """Get latency metrics for a model"""
        with self.lock:
            model_key = f"{model_name}:{model_version}"
            if model_key not in self.latency_buffer:
                return None

            latencies = list(self.latency_buffer[model_key])
            if not latencies:
                return None

            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)

            return LatencyMetrics(
                p50_ms=sorted_latencies[int(n * 0.50)],
                p95_ms=sorted_latencies[int(n * 0.95)],
                p99_ms=sorted_latencies[int(n * 0.99)],
                p999_ms=(sorted_latencies[int(n * 0.999)] if n > 1000 else sorted_latencies[-1]),
                mean_ms=statistics.mean(latencies),
                median_ms=statistics.median(latencies),
                min_ms=min(latencies),
                max_ms=max(latencies),
                std_dev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
                sample_count=n,
            )

    def get_cost_metrics(self, model_name: str, model_version: str) -> CostMetrics | None:
        """Get cost metrics for a model"""
        with self.lock:
            model_key = f"{model_name}:{model_version}"
            if model_key not in self.models:
                return None

            # Calculate from recent inferences
            recent_inferences = [
                inf
                for inf in self.inference_buffer
                if inf.model_name == model_name and inf.model_version == model_version
            ]

            if not recent_inferences:
                return None

            total_cost = sum(inf.cost_usd for inf in recent_inferences)
            total_input_tokens = sum(inf.input_tokens for inf in recent_inferences)
            total_output_tokens = sum(inf.output_tokens for inf in recent_inferences)
            total_tokens = total_input_tokens + total_output_tokens

            return CostMetrics(
                total_cost_usd=total_cost,
                cost_per_request=total_cost / len(recent_inferences),
                cost_per_1k_tokens=(
                    total_cost / (total_tokens / 1000) if total_tokens > 0 else 0.0
                ),
                total_requests=len(recent_inferences),
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
            )

    def detect_model_drift(
        self, model_name: str, model_version: str, threshold: float = 0.1
    ) -> ModelDriftMetrics | None:
        """
        Detect model drift by comparing current predictions to baseline
        """
        with self.lock:
            model_key = f"{model_name}:{model_version}"

            # Need baseline predictions
            if model_key not in self.baseline_predictions:
                # Set current predictions as baseline
                self.baseline_predictions[model_key] = list(
                    self.current_predictions.get(model_key, [])
                )
                return None

            baseline = self.baseline_predictions[model_key]
            current = self.current_predictions.get(model_key, [])

            if len(baseline) < 100 or len(current) < 100:
                return None

            # Calculate distribution shift using STRATEGY PATTERN
            drift_score = self.drift_calculator.calculate_drift(baseline, current)

            # Determine drift status
            if drift_score < threshold:
                status = DriftStatus.NO_DRIFT
            elif drift_score < threshold * 2:
                status = DriftStatus.MINOR_DRIFT
            elif drift_score < threshold * 3:
                status = DriftStatus.MODERATE_DRIFT
            else:
                status = DriftStatus.SEVERE_DRIFT

            return ModelDriftMetrics(
                drift_status=status,
                drift_score=drift_score,
                feature_drift={},  # Placeholder for feature-level drift
                prediction_drift=drift_score,
                data_quality_score=1.0 - drift_score,
                baseline_timestamp=datetime.now(UTC) - timedelta(hours=1),
                current_timestamp=datetime.now(UTC),
                samples_analyzed=min(len(baseline), len(current)),
            )

    def _group_by_sensitive_attribute(
        self,
        predictions: list[Any],
        ground_truths: list[Any],
        sensitive_attributes: list[Any],
    ) -> dict[Any, dict[str, list[Any]]]:
        """Group predictions and truths by sensitive attribute."""
        groups: dict[Any, dict[str, list[Any]]] = defaultdict(lambda: {"pred": [], "truth": []})

        for pred, truth, attr in zip(
            predictions, ground_truths, sensitive_attributes, strict=False
        ):
            groups[attr]["pred"].append(pred)
            groups[attr]["truth"].append(truth)

        return groups

    def _calculate_group_rates(
        self, preds: list[Any], truths: list[Any], positive_class: Any
    ) -> dict[str, float]:
        """Calculate positive rate, TPR, and FPR for a group."""
        pos_rate = sum(1 for p in preds if p == positive_class) / len(preds)

        tp = sum(
            1
            for p, t in zip(preds, truths, strict=False)
            if p == positive_class and t == positive_class
        )
        actual_positives = sum(1 for t in truths if t == positive_class)
        tpr = tp / actual_positives if actual_positives > 0 else 0.0

        fp = sum(
            1
            for p, t in zip(preds, truths, strict=False)
            if p == positive_class and t != positive_class
        )
        actual_negatives = sum(1 for t in truths if t != positive_class)
        fpr = fp / actual_negatives if actual_negatives > 0 else 0.0

        return {"pos_rate": pos_rate, "tpr": tpr, "fpr": fpr}

    def _calculate_demographic_parity(self, pos_rates: list[float]) -> float:
        """Calculate demographic parity metric."""
        return min(pos_rates) / max(pos_rates) if max(pos_rates) > 0 else 1.0

    def _calculate_equal_opportunity(self, tprs: list[float]) -> float:
        """Calculate equal opportunity metric."""
        return 1.0 - (max(tprs) - min(tprs))

    def _calculate_equalized_odds(self, tprs: list[float], fprs: list[float]) -> float:
        """Calculate equalized odds metric."""
        tpr_diff = max(tprs) - min(tprs)
        fpr_diff = max(fprs) - min(fprs)
        return 1.0 - ((tpr_diff + fpr_diff) / 2.0)

    def _calculate_disparate_impact(self, pos_rates: list[float]) -> float:
        """Calculate disparate impact metric."""
        return min(pos_rates) / max(pos_rates) if max(pos_rates) > 0 else 1.0

    def calculate_fairness_metrics(
        self,
        predictions: list[Any],
        ground_truths: list[Any],
        sensitive_attributes: list[Any],
        positive_class: Any = 1,
    ) -> FairnessMetrics:
        """
        Calculate fairness metrics across sensitive attributes.
        """
        groups = self._group_by_sensitive_attribute(
            predictions, ground_truths, sensitive_attributes
        )

        group_metrics = {
            group: self._calculate_group_rates(data["pred"], data["truth"], positive_class)
            for group, data in groups.items()
        }

        if len(group_metrics) < 2:
            return FairnessMetrics(
                demographic_parity=1.0,
                equal_opportunity=1.0,
                equalized_odds=1.0,
                disparate_impact=1.0,
                statistical_parity_difference=0.0,
                groups_analyzed=list(groups.keys()),
                sample_count=len(predictions),
            )

        pos_rates = [m["pos_rate"] for m in group_metrics.values()]
        tprs = [m["tpr"] for m in group_metrics.values()]
        fprs = [m["fpr"] for m in group_metrics.values()]

        return FairnessMetrics(
            demographic_parity=self._calculate_demographic_parity(pos_rates),
            equal_opportunity=self._calculate_equal_opportunity(tprs),
            equalized_odds=self._calculate_equalized_odds(tprs, fprs),
            disparate_impact=self._calculate_disparate_impact(pos_rates),
            statistical_parity_difference=max(pos_rates) - min(pos_rates),
            groups_analyzed=list(groups.keys()),
            sample_count=len(predictions),
        )

    def get_model_performance_snapshot(
        self, model_name: str, model_version: str
    ) -> ModelPerformanceSnapshot | None:
        """Get complete model performance snapshot"""
        with self.lock:
            model_key = f"{model_name}:{model_version}"
            if model_key not in self.models:
                return None

            latency = self.get_latency_metrics(model_name, model_version)
            cost = self.get_cost_metrics(model_name, model_version)
            drift = self.detect_model_drift(model_name, model_version)

            if not latency or not cost:
                return None

            # Calculate health score (0-100)
            health_score = self._calculate_health_score(latency, cost, drift)

            # Generate recommendations
            recommendations = self._generate_recommendations(latency, cost, drift)

            return ModelPerformanceSnapshot(
                model_name=model_name,
                model_version=model_version,
                timestamp=datetime.now(UTC),
                accuracy_metrics=None,  # Requires ground truth
                nlp_metrics=None,  # Requires reference texts
                latency_metrics=latency,
                cost_metrics=cost,
                drift_metrics=drift,
                fairness_metrics=None,  # Requires sensitive attributes
                health_score=health_score,
                recommendations=recommendations,
            )

    def _calculate_health_score(
        self,
        latency: LatencyMetrics,
        cost: CostMetrics,
        drift: ModelDriftMetrics | None,
    ) -> float:
        """Calculate overall model health score (0-100)"""
        score = 100.0

        # Latency penalty (target: < 100ms for P95)
        if latency.p95_ms > 100:
            score -= min(30, (latency.p95_ms - 100) / 10)

        # Cost penalty (if cost is very high)
        if cost.cost_per_request > 0.01:  # > $0.01 per request
            score -= min(20, cost.cost_per_request * 100)

        # Drift penalty
        if drift:
            if drift.drift_status == DriftStatus.SEVERE_DRIFT:
                score -= 30
            elif drift.drift_status == DriftStatus.MODERATE_DRIFT:
                score -= 20
            elif drift.drift_status == DriftStatus.MINOR_DRIFT:
                score -= 10

        return max(0.0, score)

    def _generate_recommendations(
        self,
        latency: LatencyMetrics,
        cost: CostMetrics,
        drift: ModelDriftMetrics | None,
    ) -> list[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        if latency.p95_ms > 100:
            recommendations.append(
                "⚠️ High latency detected. Consider model optimization or scaling."
            )

        if latency.p99_ms > latency.p95_ms * 2:
            recommendations.append("⚠️ High tail latency variance. Investigate outlier requests.")

        if cost.cost_per_request > 0.01:
            recommendations.append(
                "💰 High cost per request. Consider model distillation or caching."
            )

        if drift and drift.drift_status in [
            DriftStatus.MODERATE_DRIFT,
            DriftStatus.SEVERE_DRIFT,
        ]:
            recommendations.append("🔄 Model drift detected. Retrain model with recent data.")

        if not recommendations:
            recommendations.append("✅ Model performance is optimal.")

        return recommendations

    def export_metrics_summary(self) -> dict[str, Any]:
        """Export comprehensive metrics summary"""
        with self.lock:
            summary: dict[str, Any] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_models": len(self.models),
                "total_inferences": len(self.inference_buffer),
                "models": {},
            }

            for model_key, model_data in self.models.items():
                model_name = model_data["model_name"]
                model_version = model_data["model_version"]

                snapshot = self.get_model_performance_snapshot(model_name, model_version)

                if snapshot:
                    summary["models"][model_key] = {
                        "model_name": model_name,
                        "model_version": model_version,
                        "inference_count": model_data["inference_count"],
                        "error_count": model_data["error_count"],
                        "health_score": snapshot.health_score,
                        "latency": {
                            "p50_ms": snapshot.latency_metrics.p50_ms,
                            "p95_ms": snapshot.latency_metrics.p95_ms,
                            "p99_ms": snapshot.latency_metrics.p99_ms,
                        },
                        "cost": {
                            "total_usd": snapshot.cost_metrics.total_cost_usd,
                            "per_request": snapshot.cost_metrics.cost_per_request,
                        },
                        "drift": (
                            {
                                "status": snapshot.drift_metrics.drift_status.value,
                                "score": snapshot.drift_metrics.drift_score,
                            }
                            if snapshot.drift_metrics
                            else None
                        ),
                        "recommendations": snapshot.recommendations,
                    }

            return summary

# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_ai_model_service: AIModelMetricsService | None = None
_service_lock = threading.Lock()


def get_ai_model_service() -> AIModelMetricsService:
    """Get singleton AI model metrics service instance"""
    global _ai_model_service
    if _ai_model_service is None:
        with _service_lock:
            if _ai_model_service is None:
                _ai_model_service = AIModelMetricsService()
    return _ai_model_service
