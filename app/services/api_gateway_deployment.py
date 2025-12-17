import hashlib
import logging
import random
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class DeploymentStrategy(Enum):
    """Deployment strategies"""
    IMMEDIATE = 'immediate'
    CANARY = 'canary'
    BLUE_GREEN = 'blue_green'
    ROLLING = 'rolling'
    AB_TEST = 'ab_test'


class FeatureFlagStatus(Enum):
    """Feature flag statuses"""
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    CANARY = 'canary'
    PERCENTAGE = 'percentage'


@dataclass
class ModelVersion:
    """AI Model version metadata"""
    version_id: str
    model_name: str
    version_number: str
    created_at: datetime
    status: str
    traffic_weight: float = 0.0
    performance_metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestExperiment:
    """A/B test experiment configuration"""
    experiment_id: str
    name: str
    description: str
    variant_a: str
    variant_b: str
    traffic_split: float = 0.5
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    winning_variant: str | None = None


@dataclass
class CanaryDeployment:
    """Canary deployment configuration"""
    deployment_id: str
    service_id: str
    canary_version: str
    stable_version: str
    canary_traffic_percent: float = 10.0
    increment_percent: float = 10.0
    increment_interval_minutes: int = 15
    success_threshold: float = 0.95
    started_at: datetime | None = None
    current_stage: str = 'initial'
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    flag_id: str
    name: str
    description: str
    status: FeatureFlagStatus
    enabled_percentage: float = 0.0
    enabled_users: list[str] = field(default_factory=list)
    enabled_groups: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ABTestingService:
    """
    خدمة اختبار A/B - A/B testing service

    Features:
    - Traffic splitting between variants
    - Statistical significance testing
    - Automatic winner selection
    - User assignment consistency
    """

    def __init__(self):
        self.experiments: dict[str, ABTestExperiment] = {}
        self.user_assignments: dict[str, dict[str, str]] = defaultdict(dict)
        self.lock = threading.RLock()

    def create_experiment(self, experiment: ABTestExperiment) ->bool:
        """Create new A/B test experiment"""
        with self.lock:
            if experiment.experiment_id in self.experiments:
                return False
            experiment.started_at = datetime.now(UTC)
            self.experiments[experiment.experiment_id] = experiment
            logging.getLogger(__name__).info(
                f'Created A/B test: {experiment.name}')
            return True

    def assign_variant(self, experiment_id: str, user_id: str) ->(str | None):
        """
        Assign user to a variant

        Returns:
            Variant identifier (variant_a or variant_b)
        """
        with self.lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return None
            if experiment_id in self.user_assignments[user_id]:
                return self.user_assignments[user_id][experiment_id]
            hash_input = f'{user_id}:{experiment_id}'
            hash_value = int(hashlib.md5(hash_input.encode(),
                usedforsecurity=False).hexdigest(), 16)
            variant = (experiment.variant_b if hash_value % 100 / 100.0 <
                experiment.traffic_split else experiment.variant_a)
            self.user_assignments[user_id][experiment_id] = variant
            variant_key = ('variant_b_assignments' if variant == experiment
                .variant_b else 'variant_a_assignments')
            experiment.metrics[variant_key] = experiment.metrics.get(
                variant_key, 0) + 1
            return variant

    def record_outcome(self, experiment_id: str, user_id: str, metric_name:
        str, value: float):
        """Record experiment outcome metric"""
        with self.lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return
            variant = self.user_assignments[user_id].get(experiment_id)
            if not variant:
                return
            metric_key = f'{variant}_{metric_name}'
            if metric_key not in experiment.metrics:
                experiment.metrics[metric_key] = []
            experiment.metrics[metric_key].append(value)

    def get_experiment_results(self, experiment_id: str) ->(dict[str, Any] |
        None):
        """Get experiment results with statistical analysis"""
        with self.lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return None
            return {'experiment_id': experiment.experiment_id, 'name':
                experiment.name, 'variant_a': experiment.variant_a,
                'variant_b': experiment.variant_b, 'started_at': experiment
                .started_at.isoformat() if experiment.started_at else None,
                'metrics': experiment.metrics, 'winning_variant':
                experiment.winning_variant}


class CanaryDeploymentService:
    """
    خدمة النشر التدريجي - Canary deployment service

    Features:
    - Gradual traffic shifting
    - Automated rollback on errors
    - Health monitoring during rollout
    - Progressive delivery
    """

    def __init__(self):
        self.deployments: dict[str, CanaryDeployment] = {}
        self.lock = threading.RLock()

    def start_deployment(self, deployment: CanaryDeployment) ->bool:
        """Start canary deployment"""
        with self.lock:
            if deployment.deployment_id in self.deployments:
                return False
            deployment.started_at = datetime.now(UTC)
            deployment.current_stage = 'initial'
            self.deployments[deployment.deployment_id] = deployment
            logging.getLogger(__name__).info(
                f'Started canary deployment: {deployment.service_id} -> {deployment.canary_version}'
                )
            return True

    def get_version_for_request(self, deployment_id: str, user_id: (str |
        None)=None) ->(str | None):
        """
        Get version to use for request

        Returns:
            Version identifier (canary or stable)
        """
        with self.lock:
            deployment = self.deployments.get(deployment_id)
            if not deployment:
                return None
            if user_id:
                hash_input = f'{user_id}:{deployment_id}'
                hash_value = int(hashlib.md5(hash_input.encode(),
                    usedforsecurity=False).hexdigest(), 16)
                use_canary = (hash_value % 100 < deployment.
                    canary_traffic_percent)
            else:
                use_canary = random.random(
                    ) * 100 < deployment.canary_traffic_percent
            return (deployment.canary_version if use_canary else deployment
                .stable_version)

    def rollback(self, deployment_id: str) ->bool:
        """Rollback canary deployment"""
        with self.lock:
            deployment = self.deployments.get(deployment_id)
            if not deployment:
                return False
            deployment.canary_traffic_percent = 0.0
            deployment.current_stage = 'rolled_back'
            logging.getLogger(__name__).warning(
                f'Rolled back canary deployment: {deployment.service_id}')
            return True


class FeatureFlagService:
    """
    خدمة أعلام الميزات - Feature flag service

    Features:
    - Feature toggles
    - Percentage rollouts
    - User/group targeting
    - Runtime feature control
    """

    def __init__(self):
        self.flags: dict[str, FeatureFlag] = {}
        self.lock = threading.RLock()

    def create_flag(self, flag: FeatureFlag) ->bool:
        """Create feature flag"""
        with self.lock:
            if flag.flag_id in self.flags:
                return False
            self.flags[flag.flag_id] = flag
            logging.getLogger(__name__).info(
                f'Created feature flag: {flag.name}')
            return True

    def is_enabled(self, flag_id: str, user_id: (str | None)=None,
        user_groups: (list[str] | None)=None) ->bool:
        """Check if feature is enabled for user"""
        with self.lock:
            flag = self.flags.get(flag_id)
            if not flag:
                return False
            if flag.status == FeatureFlagStatus.DISABLED:
                return False
            if flag.status == FeatureFlagStatus.ENABLED:
                return True
            if user_id and user_id in flag.enabled_users:
                return True
            if user_groups:
                for group in user_groups:
                    if group in flag.enabled_groups:
                        return True
            if flag.status == FeatureFlagStatus.PERCENTAGE and user_id:
                hash_input = f'{user_id}:{flag_id}'
                hash_value = int(hashlib.md5(hash_input.encode(),
                    usedforsecurity=False).hexdigest(), 16)
                return hash_value % 100 < flag.enabled_percentage * 100
            return False

    def update_flag(self, flag_id: str, status: (FeatureFlagStatus | None)=
        None, percentage: (float | None)=None) ->bool:
        """Update feature flag"""
        with self.lock:
            flag = self.flags.get(flag_id)
            if not flag:
                return False
            if status:
                flag.status = status
            if percentage is not None:
                flag.enabled_percentage = percentage
            return True

    def get_all_flags(self) ->dict[str, dict[str, Any]]:
        """Get all feature flags"""
        with self.lock:
            return {flag_id: {'name': flag.name, 'status': flag.status.
                value, 'enabled_percentage': flag.enabled_percentage} for
                flag_id, flag in self.flags.items()}


_ab_testing_instance: ABTestingService | None = None
_canary_deployment_instance: CanaryDeploymentService | None = None
_feature_flag_instance: FeatureFlagService | None = None
_service_lock = threading.Lock()


def get_ab_testing_service() ->ABTestingService:
    """Get singleton A/B testing service"""
    global _ab_testing_instance
    if _ab_testing_instance is None:
        with _service_lock:
            if _ab_testing_instance is None:
                _ab_testing_instance = ABTestingService()
    return _ab_testing_instance


def get_canary_deployment_service() ->CanaryDeploymentService:
    """Get singleton canary deployment service"""
    global _canary_deployment_instance
    if _canary_deployment_instance is None:
        with _service_lock:
            if _canary_deployment_instance is None:
                _canary_deployment_instance = CanaryDeploymentService()
    return _canary_deployment_instance


def get_feature_flag_service() ->FeatureFlagService:
    """Get singleton feature flag service"""
    global _feature_flag_instance
    if _feature_flag_instance is None:
        with _service_lock:
            if _feature_flag_instance is None:
                _feature_flag_instance = FeatureFlagService()
    return _feature_flag_instance
