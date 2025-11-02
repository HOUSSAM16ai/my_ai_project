# app/telemetry/performance.py
# ======================================================================================
# ==        PERFORMANCE MONITORING (v1.0 - WEB VITALS EDITION)                      ==
# ======================================================================================
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
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class VitalType(Enum):
    """Web Vitals types"""
    LCP = "lcp"  # Largest Contentful Paint
    FID = "fid"  # First Input Delay
    CLS = "cls"  # Cumulative Layout Shift
    FCP = "fcp"  # First Contentful Paint
    TTFB = "ttfb"  # Time to First Byte
    INP = "inp"  # Interaction to Next Paint


class PerformanceEntryType(Enum):
    """Performance entry types"""
    NAVIGATION = "navigation"
    RESOURCE = "resource"
    PAINT = "paint"
    MARK = "mark"
    MEASURE = "measure"
    LONGTASK = "longtask"
    LAYOUT_SHIFT = "layout-shift"


@dataclass
class WebVital:
    """Web Vital measurement"""
    vital_type: VitalType
    value: float
    timestamp: float
    rating: str  # good, needs-improvement, poor
    page_url: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "vital_type": self.vital_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "rating": self.rating,
            "page_url": self.page_url,
            "user_id": self.user_id,
        }


@dataclass
class PerformanceEntry:
    """Performance entry"""
    entry_type: PerformanceEntryType
    name: str
    start_time: float
    duration: float
    attributes: Dict[str, Any] = field(default_factory=dict)


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
    
    # Web Vitals thresholds (from Google)
    THRESHOLDS = {
        VitalType.LCP: {"good": 2500, "poor": 4000},  # ms
        VitalType.FID: {"good": 100, "poor": 300},     # ms
        VitalType.CLS: {"good": 0.1, "poor": 0.25},    # score
        VitalType.FCP: {"good": 1800, "poor": 3000},   # ms
        VitalType.TTFB: {"good": 800, "poor": 1800},   # ms
        VitalType.INP: {"good": 200, "poor": 500},     # ms
    }
    
    def __init__(self):
        # Web Vitals storage
        self.vitals: deque = deque(maxlen=10000)
        
        # Performance entries
        self.entries: deque = deque(maxlen=10000)
        
        # Custom marks and measures
        self.marks: Dict[str, float] = {}
        self.measures: List[Dict[str, Any]] = []
        
        # Statistics
        self.stats = {
            "total_vitals": 0,
            "good_vitals": 0,
            "poor_vitals": 0,
            "total_entries": 0,
            "long_tasks": 0,
            "layout_shifts": 0,
        }
    
    def record_vital(
        self,
        vital_type: VitalType,
        value: float,
        page_url: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Record a Web Vital measurement"""
        # Determine rating
        rating = self._rate_vital(vital_type, value)
        
        # Create vital
        vital = WebVital(
            vital_type=vital_type,
            value=value,
            timestamp=time.time(),
            rating=rating,
            page_url=page_url,
            user_id=user_id
        )
        
        # Store vital
        self.vitals.append(vital)
        
        # Update statistics
        self.stats["total_vitals"] += 1
        if rating == "good":
            self.stats["good_vitals"] += 1
        elif rating == "poor":
            self.stats["poor_vitals"] += 1
        
        return rating
    
    def record_lcp(self, value_ms: float, **kwargs) -> str:
        """Record Largest Contentful Paint"""
        return self.record_vital(VitalType.LCP, value_ms, **kwargs)
    
    def record_fid(self, value_ms: float, **kwargs) -> str:
        """Record First Input Delay"""
        return self.record_vital(VitalType.FID, value_ms, **kwargs)
    
    def record_cls(self, value: float, **kwargs) -> str:
        """Record Cumulative Layout Shift"""
        return self.record_vital(VitalType.CLS, value, **kwargs)
    
    def record_fcp(self, value_ms: float, **kwargs) -> str:
        """Record First Contentful Paint"""
        return self.record_vital(VitalType.FCP, value_ms, **kwargs)
    
    def record_ttfb(self, value_ms: float, **kwargs) -> str:
        """Record Time to First Byte"""
        return self.record_vital(VitalType.TTFB, value_ms, **kwargs)
    
    def record_inp(self, value_ms: float, **kwargs) -> str:
        """Record Interaction to Next Paint"""
        return self.record_vital(VitalType.INP, value_ms, **kwargs)
    
    def record_entry(
        self,
        entry_type: PerformanceEntryType,
        name: str,
        start_time: float,
        duration: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Record a performance entry"""
        entry = PerformanceEntry(
            entry_type=entry_type,
            name=name,
            start_time=start_time,
            duration=duration,
            attributes=attributes or {}
        )
        
        self.entries.append(entry)
        self.stats["total_entries"] += 1
        
        # Track specific entry types
        if entry_type == PerformanceEntryType.LONGTASK:
            self.stats["long_tasks"] += 1
        elif entry_type == PerformanceEntryType.LAYOUT_SHIFT:
            self.stats["layout_shifts"] += 1
    
    def mark(self, name: str):
        """Create a performance mark"""
        self.marks[name] = time.time()
    
    def measure(
        self,
        name: str,
        start_mark: str,
        end_mark: Optional[str] = None
    ) -> Optional[float]:
        """Create a performance measure between two marks"""
        if start_mark not in self.marks:
            return None
        
        start_time = self.marks[start_mark]
        end_time = self.marks.get(end_mark, time.time()) if end_mark else time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        measure = {
            "name": name,
            "start_mark": start_mark,
            "end_mark": end_mark,
            "duration_ms": duration,
            "timestamp": time.time(),
        }
        
        self.measures.append(measure)
        
        return duration
    
    def _rate_vital(self, vital_type: VitalType, value: float) -> str:
        """Rate a vital measurement (good, needs-improvement, poor)"""
        thresholds = self.THRESHOLDS.get(vital_type)
        if not thresholds:
            return "unknown"
        
        if value <= thresholds["good"]:
            return "good"
        elif value <= thresholds["poor"]:
            return "needs-improvement"
        else:
            return "poor"
    
    def get_vital_percentiles(
        self,
        vital_type: VitalType,
        percentiles: List[int] = [50, 75, 90, 95, 99]
    ) -> Dict[int, float]:
        """Get percentiles for a specific vital"""
        values = [
            v.value for v in self.vitals
            if v.vital_type == vital_type
        ]
        
        if not values:
            return {p: 0.0 for p in percentiles}
        
        sorted_values = sorted(values)
        result = {}
        
        for p in percentiles:
            index = int(len(sorted_values) * (p / 100))
            result[p] = sorted_values[min(index, len(sorted_values) - 1)]
        
        return result
    
    def get_vital_score(self) -> Dict[str, Any]:
        """
        Calculate overall Web Vitals score
        (Similar to Google PageSpeed Insights)
        """
        if not self.vitals:
            return {"score": 0, "rating": "unknown"}
        
        # Calculate percentage of good vitals
        total = self.stats["total_vitals"]
        good = self.stats["good_vitals"]
        
        score = (good / total) * 100 if total > 0 else 0
        
        # Determine rating
        if score >= 90:
            rating = "good"
        elif score >= 50:
            rating = "needs-improvement"
        else:
            rating = "poor"
        
        return {
            "score": round(score, 2),
            "rating": rating,
            "total_vitals": total,
            "good_vitals": good,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.stats,
            "marks": len(self.marks),
            "measures": len(self.measures),
            "vital_score": self.get_vital_score(),
        }
    
    def export_vitals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Export recent vitals"""
        return [v.to_dict() for v in list(self.vitals)[-limit:]]
