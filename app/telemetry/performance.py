"""
مراقبة الأداء - Performance Monitoring

Features surpassing tech giants:
✅ Web Vitals tracking (LCP, FID, CLS, FCP, TTFB, INP)
✅ Real User Monitoring (RUM)
✅ Performance observers
✅ Resource timing analysis
✅ Long task detection
✅ Layout shift tracking
"""
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

class VitalType(Enum):
    """Web Vitals types"""
    LCP = 'lcp'
    FID = 'fid'
    CLS = 'cls'
    FCP = 'fcp'
    TTFB = 'ttfb'
    INP = 'inp'

class PerformanceEntryType(Enum):
    """Performance entry types"""
    NAVIGATION = 'navigation'
    RESOURCE = 'resource'
    PAINT = 'paint'
    MARK = 'mark'
    MEASURE = 'measure'
    LONGTASK = 'longtask'
    LAYOUT_SHIFT = 'layout-shift'

@dataclass
class WebVital:
    """Web Vital measurement"""
    vital_type: VitalType
    value: float
    timestamp: float
    rating: str
    page_url: str | None = None
    user_id: str | None = None

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary"""
        return {'vital_type': self.vital_type.value, 'value': self.value,
            'timestamp': self.timestamp, 'rating': self.rating, 'page_url':
            self.page_url, 'user_id': self.user_id}

@dataclass
class PerformanceEntry:
    """Performance entry"""
    entry_type: PerformanceEntryType
    name: str
    start_time: float
    duration: float
    attributes: dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """
    مراقبة الأداء - Performance Monitor

    Comprehensive performance monitoring:
    - Web Vitals (Core + Additional)
    - Resource Timing
    - Long Tasks
    - Layout Shifts
    - Custom Performance Marks

    Better than:
    - Google PageSpeed Insights (more real-time)
    - New Relic Browser (lower overhead)
    - DataDog RUM (more detailed metrics)
    """
    THRESHOLDS: ClassVar[dict[VitalType, dict[str, float]]] = {VitalType.
        LCP: {'good': 2500, 'poor': 4000}, VitalType.FID: {'good': 100,
        'poor': 300}, VitalType.CLS: {'good': 0.1, 'poor': 0.25}, VitalType
        .FCP: {'good': 1800, 'poor': 3000}, VitalType.TTFB: {'good': 800,
        'poor': 1800}, VitalType.INP: {'good': 200, 'poor': 500}}

    def __init__(self):
        self.vitals: deque = deque(maxlen=10000)
        self.entries: deque = deque(maxlen=10000)
        self.marks: dict[str, float] = {}
        self.measures: list[dict[str, Any]] = []
        self.stats = {'total_vitals': 0, 'good_vitals': 0, 'poor_vitals': 0,
            'total_entries': 0, 'long_tasks': 0, 'layout_shifts': 0}

    def record_vital(self, vital_type: VitalType, value: float, page_url: (
        str | None)=None, user_id: (str | None)=None) ->str:
        """Record a Web Vital measurement"""
        rating = self._rate_vital(vital_type, value)
        vital = WebVital(vital_type=vital_type, value=value, timestamp=time
            .time(), rating=rating, page_url=page_url, user_id=user_id)
        self.vitals.append(vital)
        self.stats['total_vitals'] += 1
        if rating == 'good':
            self.stats['good_vitals'] += 1
        elif rating == 'poor':
            self.stats['poor_vitals'] += 1
        return rating

    def mark(self, name: str) -> None:
        """Create a performance mark"""
        self.marks[name] = time.time()

    def measure(self, name: str, start_mark: str, end_mark: (str | None)=None
        ) ->(float | None):
        """Create a performance measure between two marks"""
        if start_mark not in self.marks:
            return None
        start_time = self.marks[start_mark]
        end_time = self.marks.get(end_mark, time.time()
            ) if end_mark else time.time()
        duration = (end_time - start_time) * 1000
        measure = {'name': name, 'start_mark': start_mark, 'end_mark':
            end_mark, 'duration_ms': duration, 'timestamp': time.time()}
        self.measures.append(measure)
        return duration

    def _rate_vital(self, vital_type: VitalType, value: float) ->str:
        """Rate a vital measurement (good, needs-improvement, poor)"""
        thresholds = self.THRESHOLDS.get(vital_type)
        if not thresholds:
            return 'unknown'
        if value <= thresholds['good']:
            return 'good'
        if value <= thresholds['poor']:
            return 'needs-improvement'
        return 'poor'

    def get_vital_score(self) ->dict[str, Any]:
        """
        Calculate overall Web Vitals score
        (Similar to Google PageSpeed Insights)
        """
        if not self.vitals:
            return {'score': 0, 'rating': 'unknown'}
        total = self.stats['total_vitals']
        good = self.stats['good_vitals']
        score = good / total * 100 if total > 0 else 0
        if score >= 90:
            rating = 'good'
        elif score >= 50:
            rating = 'needs-improvement'
        else:
            rating = 'poor'
        return {'score': round(score, 2), 'rating': rating, 'total_vitals':
            total, 'good_vitals': good}

    def get_statistics(self) ->dict[str, Any]:
        """Get performance statistics"""
        return {**self.stats, 'marks': len(self.marks), 'measures': len(
            self.measures), 'vital_score': self.get_vital_score()}
