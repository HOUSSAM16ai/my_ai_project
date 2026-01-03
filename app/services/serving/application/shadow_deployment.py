"""
Shadow Deployment Manager
==========================
Manages shadow deployments for testing new models in production without affecting users.
"""
from __future__ import annotations

from typing import Any


import threading
import uuid
from typing import TYPE_CHECKING

from app.services.serving.domain.models import ShadowDeployment

if TYPE_CHECKING:
    pass

class ShadowDeploymentManager:
    """
    Shadow Deployment Manager - مدير النشر الخفي

    Responsibilities:
    - Create and manage shadow deployments
    - Route traffic to shadow models in background
    - Collect comparison data between primary and shadow models
    """

    def __init__(self):
        self._shadow_deployments: dict[str, ShadowDeployment] = {}
        self._lock = threading.RLock()

    def start_shadow_deployment(self, primary_model_id: str,
        shadow_model_id: str, traffic_percentage: float=100.0) ->str:
        """
        بدء نشر في الوضع الخفي (Shadow Mode)

        Args:
            primary_model_id: النموذج الأساسي (الإنتاج)
            shadow_model_id: النموذج الخفي (الاختبار)
            traffic_percentage: نسبة الطلبات لنسخها

        Returns:
            معرف النشر الخفي
        """
        shadow_id = str(uuid.uuid4())
        deployment = ShadowDeployment(shadow_id=shadow_id, primary_model_id
            =primary_model_id, shadow_model_id=shadow_model_id,
            traffic_percentage=traffic_percentage)
        with self._lock:
            self._shadow_deployments[shadow_id] = deployment
        return shadow_id

    def get_shadow_deployment_stats(self, shadow_id: str) -> dict[str, Any] | None:
        """
        الحصول على إحصائيات النشر الخفي
        Get shadow deployment statistics
        
        Args:
            shadow_id: معرف النشر الخفي | Shadow deployment ID
            
        Returns:
            إحصائيات النشر أو None | Deployment statistics or None
        """
        deployment = self._shadow_deployments.get(shadow_id)
        if not deployment:
            return None
        
        # Get comparison results
        comparisons = self._get_deployment_comparisons(deployment)
        
        if not comparisons:
            return self._create_empty_stats_response(shadow_id)
        
        # Calculate statistics
        return self._calculate_deployment_statistics(shadow_id, deployment, comparisons)

    def _get_deployment_comparisons(self, deployment: ShadowDeployment) -> list[dict[str, Any]]:
        """
        الحصول على نتائج المقارنة | Get comparison results
        
        Args:
            deployment: النشر الخفي | Shadow deployment
            
        Returns:
            قائمة نتائج المقارنة | Comparison results list
        """
        with self._lock:
            return deployment.comparison_results.copy()

    def _create_empty_stats_response(self, shadow_id: str) -> dict[str, Any]:
        """
        إنشاء استجابة فارغة للإحصائيات | Create empty stats response
        
        Args:
            shadow_id: معرف النشر | Deployment ID
            
        Returns:
            استجابة فارغة | Empty response
        """
        return {
            'shadow_id': shadow_id,
            'total_comparisons': 0,
            'message': 'No comparisons yet'
        }

    def _calculate_deployment_statistics(
        self,
        shadow_id: str,
        deployment: ShadowDeployment,
        comparisons: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        حساب إحصائيات النشر | Calculate deployment statistics
        
        Args:
            shadow_id: معرف النشر | Deployment ID
            deployment: النشر الخفي | Shadow deployment
            comparisons: نتائج المقارنة | Comparison results
            
        Returns:
            الإحصائيات المحسوبة | Calculated statistics
        """
        total = len(comparisons)
        
        # Calculate speed comparison
        primary_faster = sum(
            1 for c in comparisons
            if c['primary_latency'] < c['shadow_latency']
        )
        shadow_faster = total - primary_faster
        
        # Calculate success rates
        primary_success_rate = (
            sum(1 for c in comparisons if c['primary_success']) / total * 100
        )
        shadow_success_rate = (
            sum(1 for c in comparisons if c['shadow_success']) / total * 100
        )
        
        return {
            'shadow_id': shadow_id,
            'primary_model_id': deployment.primary_model_id,
            'shadow_model_id': deployment.shadow_model_id,
            'total_comparisons': total,
            'primary_faster_count': primary_faster,
            'shadow_faster_count': shadow_faster,
            'primary_success_rate': primary_success_rate,
            'shadow_success_rate': shadow_success_rate,
            'started_at': deployment.started_at.isoformat()
        }
