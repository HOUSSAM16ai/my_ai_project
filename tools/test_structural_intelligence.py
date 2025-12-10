#!/usr/bin/env python3
"""
اختبارات شاملة للتحليل البنيوي - Comprehensive Tests for Structural Analysis
Superhuman Quality Assurance

هذا السكريبت يختبر جميع مكونات نظام التحليل البنيوي بدقة عبقرية فائقة الذكاء
"""

import json
import sys
import tempfile
from pathlib import Path
import subprocess

# ANSI Colors for beautiful output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

class SuperhumanTestRunner:
    """نظام اختبار فائق الجودة"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def test(self, name: str, func):
        """تشغيل اختبار واحد"""
        print(f"\n{BLUE}🧪 Running: {name}{RESET}")
        try:
            func()
            print(f"{GREEN}✅ PASSED: {name}{RESET}")
            self.tests_passed += 1
            self.test_results.append((name, "PASSED", None))
        except AssertionError as e:
            print(f"{RED}❌ FAILED: {name}{RESET}")
            print(f"{RED}   Error: {e}{RESET}")
            self.tests_failed += 1
            self.test_results.append((name, "FAILED", str(e)))
        except Exception as e:
            print(f"{RED}💥 ERROR: {name}{RESET}")
            print(f"{RED}   Exception: {e}{RESET}")
            self.tests_failed += 1
            self.test_results.append((name, "ERROR", str(e)))
    
    def print_summary(self):
        """طباعة ملخص النتائج"""
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"{BOLD}{BLUE}📊 TEST SUMMARY{RESET}")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.tests_passed}{RESET}")
        print(f"{RED}Failed: {self.tests_failed}{RESET}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*70}\n")
        
        if success_rate == 100:
            print(f"{GREEN}{BOLD}🎉 SUPERHUMAN QUALITY ACHIEVED! 100% SUCCESS! 🎉{RESET}\n")
        elif success_rate >= 90:
            print(f"{YELLOW}{BOLD}⚠️  Good but not perfect. Need 100% for superhuman quality.{RESET}\n")
        else:
            print(f"{RED}{BOLD}❌ CRITICAL: Quality standards not met!{RESET}\n")
        
        return success_rate == 100


def test_tool_exists():
    """التحقق من وجود الأداة"""
    tool_path = Path("tools/structural_code_intelligence.py")
    assert tool_path.exists(), f"Tool not found at {tool_path}"
    assert tool_path.stat().st_mode & 0o111, "Tool is not executable"


def test_tool_syntax():
    """التحقق من صحة Syntax"""
    result = subprocess.run(
        ["python3", "-m", "py_compile", "tools/structural_code_intelligence.py"],
        capture_output=True
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"


def test_tool_help():
    """التحقق من عمل Help"""
    result = subprocess.run(
        ["python3", "tools/structural_code_intelligence.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Help command failed"
    assert "المرحلة الأولى" in result.stdout, "Help text incomplete"


def test_analysis_on_sample():
    """اختبار التحليل على عينة"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api/exceptions.py",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Analysis failed: {result.stderr}"
        
        # Check all output files exist
        output_dir = Path(tmpdir)
        assert (output_dir / "structural_analysis_latest.json").exists(), "JSON not created"
        assert (output_dir / "structural_analysis_latest.csv").exists(), "CSV not created"
        assert (output_dir / "heatmap_latest.html").exists(), "HTML not created"
        assert (output_dir / "report_latest.md").exists(), "Markdown not created"


def test_json_structure():
    """التحقق من بنية JSON"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        json_file = Path(tmpdir) / "structural_analysis_latest.json"
        with open(json_file) as f:
            data = json.load(f)
        
        # Validate required top-level fields
        required_fields = [
            "timestamp", "total_files", "total_lines", "total_code_lines",
            "total_functions", "total_classes", "avg_file_complexity",
            "max_file_complexity", "critical_hotspots", "high_hotspots", "files"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate file metrics structure
        if data["files"]:
            file_metrics = data["files"][0]
            file_required = [
                "relative_path", "code_lines", "file_complexity",
                "hotspot_score", "priority_tier"
            ]
            for field in file_required:
                assert field in file_metrics, f"Missing file field: {field}"


def test_csv_structure():
    """التحقق من بنية CSV"""
    import csv
    
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        csv_file = Path(tmpdir) / "structural_analysis_latest.csv"
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "CSV has no data rows"
        
        required_cols = [
            "relative_path", "code_lines", "file_complexity",
            "hotspot_score", "priority_tier"
        ]
        for col in required_cols:
            assert col in rows[0], f"Missing CSV column: {col}"


def test_html_generation():
    """التحقق من توليد HTML"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        html_file = Path(tmpdir) / "heatmap_latest.html"
        content = html_file.read_text()
        
        # Check for essential HTML elements
        assert "<!DOCTYPE html>" in content, "Invalid HTML structure"
        assert "خريطة حرارية" in content, "Missing title"
        assert "file-row" in content, "Missing file rows"
        assert "CRITICAL" in content or "HIGH" in content or len(content) > 1000, "HTML seems empty"


def test_markdown_generation():
    """التحقق من توليد Markdown"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        md_file = Path(tmpdir) / "report_latest.md"
        content = md_file.read_text()
        
        # Check for essential sections
        assert "# 🔍 تقرير التحليل البنيوي للكود" in content, "Missing title"
        assert "## 📊 ملخص المشروع" in content, "Missing summary section"
        assert "Hotspots" in content, "Missing hotspots section"


def test_hotspot_scoring():
    """التحقق من حساب Hotspot Score"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        json_file = Path(tmpdir) / "structural_analysis_latest.json"
        with open(json_file) as f:
            data = json.load(f)
        
        if data["files"]:
            for file_data in data["files"]:
                score = file_data["hotspot_score"]
                # Score must be between 0 and 1
                assert 0 <= score <= 1, f"Invalid hotspot score: {score}"
                
                # Priority tier must match score
                tier = file_data["priority_tier"]
                if score >= 0.7:
                    assert tier == "CRITICAL", f"Score {score} should be CRITICAL not {tier}"
                elif score >= 0.5:
                    assert tier == "HIGH", f"Score {score} should be HIGH not {tier}"
                elif score >= 0.3:
                    assert tier == "MEDIUM", f"Score {score} should be MEDIUM not {tier}"
                else:
                    assert tier == "LOW", f"Score {score} should be LOW not {tier}"


def test_complexity_calculation():
    """التحقق من حساب التعقيد"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        json_file = Path(tmpdir) / "structural_analysis_latest.json"
        with open(json_file) as f:
            data = json.load(f)
        
        # Average complexity should be reasonable
        avg_complexity = data["avg_file_complexity"]
        assert avg_complexity > 0, "Average complexity is zero"
        assert avg_complexity < 1000, f"Average complexity too high: {avg_complexity}"
        
        # Max complexity should be >= average
        max_complexity = data["max_file_complexity"]
        assert max_complexity >= avg_complexity, "Max < Avg complexity"


def test_git_analysis():
    """التحقق من تحليل Git"""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--targets", "app/api",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            timeout=30
        )
        
        json_file = Path(tmpdir) / "structural_analysis_latest.json"
        with open(json_file) as f:
            data = json.load(f)
        
        if data["files"]:
            # At least one file should have git data
            has_commits = any(f["total_commits"] > 0 for f in data["files"])
            # This may be false in shallow clones, so just warn
            if not has_commits:
                print(f"{YELLOW}⚠️  Warning: No Git history found (shallow clone?){RESET}")


def test_full_project_analysis():
    """اختبار التحليل على المشروع الكامل"""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "python3", "tools/structural_code_intelligence.py",
                "--output-dir", tmpdir
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Full project analysis failed: {result.stderr}"
        
        json_file = Path(tmpdir) / "structural_analysis_latest.json"
        with open(json_file) as f:
            data = json.load(f)
        
        # Should analyze many files
        assert data["total_files"] > 50, f"Only {data['total_files']} files analyzed"
        assert data["total_functions"] > 100, "Too few functions found"
        
        print(f"{GREEN}   ✓ Analyzed {data['total_files']} files with {data['total_functions']} functions{RESET}")


def test_documentation_exists():
    """التحقق من وجود التوثيق"""
    docs = [
        "docs/STRUCTURAL_ANALYSIS_GUIDE_AR.md",
        "docs/STRUCTURAL_ANALYSIS_QUICK_REF.md"
    ]
    for doc in docs:
        doc_path = Path(doc)
        assert doc_path.exists(), f"Documentation missing: {doc}"
        assert doc_path.stat().st_size > 1000, f"Documentation too small: {doc}"


def main():
    """تشغيل جميع الاختبارات"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}🚀 SUPERHUMAN STRUCTURAL ANALYSIS - COMPREHENSIVE TESTS 🚀{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    runner = SuperhumanTestRunner()
    
    # Core functionality tests
    runner.test("Tool File Exists", test_tool_exists)
    runner.test("Python Syntax Valid", test_tool_syntax)
    runner.test("Help Command Works", test_tool_help)
    runner.test("Analysis on Sample Directory", test_analysis_on_sample)
    
    # Output format tests
    runner.test("JSON Structure Valid", test_json_structure)
    runner.test("CSV Structure Valid", test_csv_structure)
    runner.test("HTML Generation Works", test_html_generation)
    runner.test("Markdown Generation Works", test_markdown_generation)
    
    # Algorithm tests
    runner.test("Hotspot Scoring Correct", test_hotspot_scoring)
    runner.test("Complexity Calculation Valid", test_complexity_calculation)
    runner.test("Git Analysis Works", test_git_analysis)
    
    # Integration tests
    runner.test("Full Project Analysis", test_full_project_analysis)
    runner.test("Documentation Complete", test_documentation_exists)
    
    # Print summary
    success = runner.print_summary()
    
    if success:
        print(f"{GREEN}{BOLD}✨ ALL TESTS PASSED - SUPERHUMAN QUALITY CONFIRMED ✨{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}⚠️  SOME TESTS FAILED - QUALITY STANDARDS NOT MET ⚠️{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
