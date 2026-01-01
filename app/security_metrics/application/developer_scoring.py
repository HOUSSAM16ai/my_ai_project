"""Developer security scoring use case - Single Responsibility Principle."""

import statistics
from datetime import datetime

from app.security_metrics.domain.entities import DeveloperSecurityScore
from app.security_metrics.domain.interfaces import SecurityRepository

class DeveloperSecurityScorer:
    """Developer security scorer - SRP: Only scores developers."""

    def __init__(self, repository: SecurityRepository):
        self.repository = repository

    def calculate_score(self, developer_id: str) -> DeveloperSecurityScore:
        """Calculate developer security score - Complexity < 10."""
        findings = self.repository.get_findings_by_developer(developer_id)

        if not findings:
            return self._create_empty_score(developer_id)

        findings_count = len(findings)
        fixed_count = sum(1 for f in findings if f.fixed)
        fix_rate = (fixed_count / findings_count * 100) if findings_count > 0 else 0

        fix_times = [f.fix_time_hours for f in findings if f.fix_time_hours]
        avg_fix_time = statistics.mean(fix_times) if fix_times else 0

        score = self._calculate_developer_score(findings_count, fix_rate, avg_fix_time)

        return DeveloperSecurityScore(
            developer_id=developer_id,
            score=score,
            findings_count=findings_count,
            fix_rate=round(fix_rate, 2),
            avg_fix_time=round(avg_fix_time, 2),
            timestamp=datetime.now(),
        )

    def _calculate_developer_score(self, findings_count: int, fix_rate: float, avg_fix_time: float) -> float:
        """Calculate developer score - Complexity < 10."""
        base_score = 100.0

        findings_penalty = min(50, findings_count * 2)
        fix_bonus = fix_rate * 0.3
        time_penalty = min(20, avg_fix_time * 0.5)

        final_score = max(0, base_score - findings_penalty + fix_bonus - time_penalty)
        return round(final_score, 2)

    def _create_empty_score(self, developer_id: str) -> DeveloperSecurityScore:
        """Create empty score for new developers."""
        return DeveloperSecurityScore(
            developer_id=developer_id,
            score=100.0,
            findings_count=0,
            fix_rate=0.0,
            avg_fix_time=0.0,
            timestamp=datetime.now(),
        )
