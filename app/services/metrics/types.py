from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class MetricType(Enum):
    """AI metric type enumeration"""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    BLEU = "bleu"
    ROUGE = "rouge"
    PERPLEXITY = "perplexity"
    BERTSCORE = "bertscore"
    METEOR = "meteor"
    FID = "fid"  # Frechet Inception Distance
    IS = "is"  # Inception Score
    LATENCY = "latency"
    COST = "cost"
    FAIRNESS = "fairness"
    DRIFT = "drift"


class ModelType(Enum):
    """Model type enumeration"""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP_GENERATION = "nlp_generation"
    NLP_TRANSLATION = "nlp_translation"
    IMAGE_GENERATION = "image_generation"
    EMBEDDINGS = "embeddings"


class DriftStatus(Enum):
    """Model drift status"""

    NO_DRIFT = "no_drift"
    MINOR_DRIFT = "minor_drift"
    MODERATE_DRIFT = "moderate_drift"
    SEVERE_DRIFT = "severe_drift"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class InferenceMetrics:
    """Single inference metrics"""

    inference_id: str
    model_name: str
    model_version: str
    timestamp: datetime
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    prediction: Any
    ground_truth: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccuracyMetrics:
    """Classification/regression accuracy metrics"""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    confusion_matrix: list[list[int]] | None = None
    sample_count: int = 0


@dataclass
class NLPMetrics:
    """NLP-specific quality metrics"""

    bleu_score: float | None = None  # 0-1, higher is better
    rouge_1: float | None = None  # Unigram overlap
    rouge_2: float | None = None  # Bigram overlap
    rouge_l: float | None = None  # Longest common subsequence
    perplexity: float | None = None  # Lower is better
    bertscore_precision: float | None = None
    bertscore_recall: float | None = None
    bertscore_f1: float | None = None
    meteor_score: float | None = None
    sample_count: int = 0


@dataclass
class LatencyMetrics:
    """Inference latency metrics"""

    p50_ms: float
    p95_ms: float
    p99_ms: float
    p999_ms: float
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    sample_count: int


@dataclass
class CostMetrics:
    """Inference cost metrics"""

    total_cost_usd: float
    cost_per_request: float
    cost_per_1k_tokens: float
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int


@dataclass
class ModelDriftMetrics:
    """Model drift detection metrics"""

    drift_status: DriftStatus
    drift_score: float  # 0-1, higher means more drift
    feature_drift: dict[str, float]  # Feature-level drift scores
    prediction_drift: float  # Distribution shift in predictions
    data_quality_score: float
    baseline_timestamp: datetime
    current_timestamp: datetime
    samples_analyzed: int


@dataclass
class FairnessMetrics:
    """Model fairness and bias metrics"""

    demographic_parity: float  # Close to 1.0 is fair
    equal_opportunity: float  # Equal TPR across groups
    equalized_odds: float  # Equal TPR and FPR across groups
    disparate_impact: float  # Ratio of positive rates
    statistical_parity_difference: float
    groups_analyzed: list[str]
    sample_count: int


@dataclass
class ModelPerformanceSnapshot:
    """Complete model performance snapshot"""

    model_name: str
    model_version: str
    timestamp: datetime
    accuracy_metrics: AccuracyMetrics | None
    nlp_metrics: NLPMetrics | None
    latency_metrics: LatencyMetrics
    cost_metrics: CostMetrics
    drift_metrics: ModelDriftMetrics | None
    fairness_metrics: FairnessMetrics | None
    health_score: float  # 0-100
    recommendations: list[str]
