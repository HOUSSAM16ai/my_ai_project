from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileMetrics:
    """Comprehensive metrics for a single file"""

    # Basic Information
    file_path: str
    relative_path: str

    # Size Metrics
    total_lines: int = 0
    code_lines: int = 0  # Lines of Code (LOC) excluding comments and blanks
    comment_lines: int = 0
    blank_lines: int = 0
    num_classes: int = 0
    num_functions: int = 0
    num_public_functions: int = 0

    # Complexity Metrics
    file_complexity: int = 0  # Total cyclomatic complexity
    avg_function_complexity: float = 0.0
    max_function_complexity: int = 0
    max_function_name: str = ""
    complexity_std_dev: float = 0.0

    # Nesting Metrics
    max_nesting_depth: int = 0
    avg_nesting_depth: float = 0.0

    # Change Volatility
    total_commits: int = 0
    commits_last_6months: int = 0
    commits_last_12months: int = 0
    num_authors: int = 0
    bugfix_commits: int = 0
    branches_modified: int = 0

    # Structural Smells
    is_god_class: bool = False
    has_layer_mixing: bool = False
    has_cross_layer_imports: bool = False
    num_imports: int = 0
    num_external_dependencies: int = 0

    # Function Details
    function_details: list[dict[str, Any]] = field(default_factory=list)

    # Hotspot Scores
    complexity_rank: float = 0.0
    volatility_rank: float = 0.0
    smell_rank: float = 0.0
    hotspot_score: float = 0.0
    priority_tier: str = ""  # "CRITICAL", "HIGH", "MEDIUM", "LOW"

@dataclass
class ProjectAnalysis:
    """Comprehensive project analysis"""

    timestamp: str
    total_files: int
    total_lines: int
    total_code_lines: int
    total_functions: int
    total_classes: int
    avg_file_complexity: float
    max_file_complexity: int

    # Hotspots
    critical_hotspots: list[str] = field(default_factory=list)  # Top 20
    high_hotspots: list[str] = field(default_factory=list)  # Next 20

    files: list[FileMetrics] = field(default_factory=list)
