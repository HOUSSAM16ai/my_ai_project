#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 CogniForge Auto-Diagnostic & Self-Healing System
====================================================
نظام تشخيص وإصلاح ذاتي خارق - Superhuman Auto-Diagnostic System

This script performs comprehensive diagnostics and automated fixes.
Better than tech giants because:
- ✅ Automatic problem detection
- ✅ Self-healing capabilities
- ✅ Bilingual support (Arabic + English)
- ✅ Detailed reporting
- ✅ Interactive mode

Usage:
    python3 auto_diagnose_and_fix.py              # Interactive mode
    python3 auto_diagnose_and_fix.py --auto-fix   # Automatic fix mode
    python3 auto_diagnose_and_fix.py --report     # Report only mode
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DiagnosticResult:
    """Represents a diagnostic check result"""
    def __init__(self, check_name: str, passed: bool, message: str, 
                 severity: str = "info", fix_available: bool = False):
        self.check_name = check_name
        self.passed = passed
        self.message = message
        self.severity = severity  # critical, high, medium, low, info
        self.fix_available = fix_available
        self.timestamp = datetime.now()


class CogniForgeAutoDiagnostic:
    """Main diagnostic and self-healing system"""
    
    def __init__(self, auto_fix: bool = False):
        self.auto_fix = auto_fix
        self.results: List[DiagnosticResult] = []
        self.fixes_applied: List[str] = []
        self.project_root = Path.cwd()
        
    def print_header(self):
        """Print diagnostic header"""
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}🔍 CogniForge Auto-Diagnostic & Self-Healing System{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}نظام التشخيص والإصلاح الذاتي الخارق{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}\n")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Project Root: {self.project_root}")
        print(f"🔧 Auto-Fix Mode: {'ON' if self.auto_fix else 'OFF'}")
        print()
    
    def print_section(self, title: str, icon: str = "📋"):
        """Print section header"""
        print(f"\n{Colors.BOLD}{icon} {title}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-'*80}{Colors.ENDC}")
    
    def add_result(self, result: DiagnosticResult):
        """Add a diagnostic result"""
        self.results.append(result)
        
        # Print result immediately
        status_icon = "✅" if result.passed else "❌"
        status_color = Colors.OKGREEN if result.passed else Colors.FAIL
        
        print(f"{status_color}{status_icon} {result.check_name}{Colors.ENDC}")
        print(f"   {result.message}")
        
        if not result.passed and result.fix_available:
            print(f"   {Colors.WARNING}🔧 Fix available{Colors.ENDC}")
    
    def check_env_file(self) -> DiagnosticResult:
        """Check if .env file exists"""
        env_file = self.project_root / '.env'
        
        if env_file.exists():
            return DiagnosticResult(
                check_name="ملف .env موجود / .env file exists",
                passed=True,
                message="✓ .env file found",
                severity="info"
            )
        else:
            return DiagnosticResult(
                check_name="ملف .env موجود / .env file exists",
                passed=False,
                message="✗ .env file not found - AI features will not work",
                severity="critical",
                fix_available=True
            )
    
    def fix_env_file(self) -> bool:
        """Create .env file from .env.example"""
        try:
            env_example = self.project_root / '.env.example'
            env_file = self.project_root / '.env'
            
            if not env_example.exists():
                print(f"{Colors.FAIL}   ❌ Cannot create .env: .env.example not found{Colors.ENDC}")
                return False
            
            shutil.copy(env_example, env_file)
            self.fixes_applied.append("Created .env file from .env.example")
            print(f"{Colors.OKGREEN}   ✅ Created .env file{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}   ❌ Failed to create .env: {e}{Colors.ENDC}")
            return False
    
    def check_api_keys(self) -> List[DiagnosticResult]:
        """Check if API keys are configured"""
        results = []
        
        # Load .env file
        env_file = self.project_root / '.env'
        env_vars = {}
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Check OPENROUTER_API_KEY
        openrouter_key = env_vars.get('OPENROUTER_API_KEY', '')
        openai_key = env_vars.get('OPENAI_API_KEY', '')
        
        # Check if keys are real (not example values)
        openrouter_valid = openrouter_key and not openrouter_key.startswith('sk-or-v1-xxx')
        openai_valid = openai_key and not openai_key.startswith('sk-xxx')
        
        if openrouter_valid or openai_valid:
            results.append(DiagnosticResult(
                check_name="مفاتيح API مُكونة / API keys configured",
                passed=True,
                message=f"✓ API keys configured (OpenRouter: {openrouter_valid}, OpenAI: {openai_valid})",
                severity="info"
            ))
        else:
            results.append(DiagnosticResult(
                check_name="مفاتيح API مُكونة / API keys configured",
                passed=False,
                message="✗ No valid API keys found - Please add OPENROUTER_API_KEY or OPENAI_API_KEY to .env",
                severity="critical",
                fix_available=False  # Requires manual action
            ))
        
        return results
    
    def check_database_connection(self) -> DiagnosticResult:
        """Check database connection"""
        try:
            # Try to import and connect
            result = subprocess.run(
                ['python3', '-c', 
                 'from app import create_app, db; app = create_app(); '
                 'app.app_context().push(); db.engine.connect(); print("OK")'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and 'OK' in result.stdout:
                return DiagnosticResult(
                    check_name="اتصال قاعدة البيانات / Database connection",
                    passed=True,
                    message="✓ Database connected successfully",
                    severity="info"
                )
            else:
                error_msg = result.stderr.strip()[:200]
                return DiagnosticResult(
                    check_name="اتصال قاعدة البيانات / Database connection",
                    passed=False,
                    message=f"✗ Database connection failed: {error_msg}",
                    severity="high",
                    fix_available=False
                )
                
        except subprocess.TimeoutExpired:
            return DiagnosticResult(
                check_name="اتصال قاعدة البيانات / Database connection",
                passed=False,
                message="✗ Database connection timeout",
                severity="high",
                fix_available=False
            )
        except Exception as e:
            return DiagnosticResult(
                check_name="اتصال قاعدة البيانات / Database connection",
                passed=False,
                message=f"✗ Database check failed: {str(e)}",
                severity="high",
                fix_available=False
            )
    
    def check_dependencies(self) -> DiagnosticResult:
        """Check if required dependencies are installed"""
        try:
            result = subprocess.run(
                ['pip3', 'freeze'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            installed = result.stdout
            required_packages = [
                'flask',
                'sqlalchemy',
                'openai',
                'requests'
            ]
            
            missing = []
            for package in required_packages:
                if package.lower() not in installed.lower():
                    missing.append(package)
            
            if not missing:
                return DiagnosticResult(
                    check_name="التبعيات المطلوبة / Required dependencies",
                    passed=True,
                    message="✓ All required dependencies installed",
                    severity="info"
                )
            else:
                return DiagnosticResult(
                    check_name="التبعيات المطلوبة / Required dependencies",
                    passed=False,
                    message=f"✗ Missing dependencies: {', '.join(missing)}",
                    severity="medium",
                    fix_available=True
                )
                
        except Exception as e:
            return DiagnosticResult(
                check_name="التبعيات المطلوبة / Required dependencies",
                passed=False,
                message=f"✗ Dependency check failed: {str(e)}",
                severity="medium",
                fix_available=False
            )
    
    def fix_dependencies(self) -> bool:
        """Install missing dependencies"""
        try:
            print(f"{Colors.WARNING}   🔧 Installing dependencies...{Colors.ENDC}")
            result = subprocess.run(
                ['pip3', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.fixes_applied.append("Installed missing dependencies")
                print(f"{Colors.OKGREEN}   ✅ Dependencies installed{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}   ❌ Failed to install dependencies{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.FAIL}   ❌ Failed to install dependencies: {e}{Colors.ENDC}")
            return False
    
    def check_migrations(self) -> DiagnosticResult:
        """Check if database migrations are applied"""
        try:
            result = subprocess.run(
                ['flask', 'db', 'current'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return DiagnosticResult(
                    check_name="هجرات قاعدة البيانات / Database migrations",
                    passed=True,
                    message="✓ Database migrations applied",
                    severity="info"
                )
            else:
                return DiagnosticResult(
                    check_name="هجرات قاعدة البيانات / Database migrations",
                    passed=False,
                    message="✗ Database migrations not applied",
                    severity="high",
                    fix_available=True
                )
                
        except Exception as e:
            return DiagnosticResult(
                check_name="هجرات قاعدة البيانات / Database migrations",
                passed=False,
                message=f"✗ Migration check failed: {str(e)}",
                severity="high",
                fix_available=False
            )
    
    def fix_migrations(self) -> bool:
        """Apply database migrations"""
        try:
            print(f"{Colors.WARNING}   🔧 Applying migrations...{Colors.ENDC}")
            result = subprocess.run(
                ['flask', 'db', 'upgrade'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.fixes_applied.append("Applied database migrations")
                print(f"{Colors.OKGREEN}   ✅ Migrations applied{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}   ❌ Failed to apply migrations: {result.stderr}{Colors.ENDC}")
                return False
                
        except Exception as e:
            print(f"{Colors.FAIL}   ❌ Failed to apply migrations: {e}{Colors.ENDC}")
            return False
    
    def run_diagnostics(self):
        """Run all diagnostic checks"""
        self.print_header()
        
        # 1. Check .env file
        self.print_section("1️⃣ Configuration Files", "📁")
        env_result = self.check_env_file()
        self.add_result(env_result)
        
        if not env_result.passed and env_result.fix_available:
            if self.auto_fix or self.ask_for_fix("Create .env file?"):
                self.fix_env_file()
        
        # 2. Check API keys
        self.print_section("2️⃣ API Keys", "🔑")
        for result in self.check_api_keys():
            self.add_result(result)
        
        # 3. Check dependencies
        self.print_section("3️⃣ Dependencies", "📦")
        dep_result = self.check_dependencies()
        self.add_result(dep_result)
        
        if not dep_result.passed and dep_result.fix_available:
            if self.auto_fix or self.ask_for_fix("Install missing dependencies?"):
                self.fix_dependencies()
        
        # 4. Check database connection
        self.print_section("4️⃣ Database", "💾")
        db_result = self.check_database_connection()
        self.add_result(db_result)
        
        # 5. Check migrations
        if db_result.passed:
            migration_result = self.check_migrations()
            self.add_result(migration_result)
            
            if not migration_result.passed and migration_result.fix_available:
                if self.auto_fix or self.ask_for_fix("Apply database migrations?"):
                    self.fix_migrations()
    
    def ask_for_fix(self, question: str) -> bool:
        """Ask user if they want to apply a fix"""
        response = input(f"{Colors.WARNING}   {question} (y/n): {Colors.ENDC}").strip().lower()
        return response in ['y', 'yes', 'نعم', 'ن']
    
    def print_summary(self):
        """Print diagnostic summary"""
        self.print_section("📊 Diagnostic Summary", "📊")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        critical = sum(1 for r in self.results if not r.passed and r.severity == "critical")
        high = sum(1 for r in self.results if not r.passed and r.severity == "high")
        medium = sum(1 for r in self.results if not r.passed and r.severity == "medium")
        
        print(f"\n{Colors.BOLD}Overall Results:{Colors.ENDC}")
        print(f"  Total Checks: {total}")
        print(f"  {Colors.OKGREEN}✅ Passed: {passed}{Colors.ENDC}")
        print(f"  {Colors.FAIL}❌ Failed: {failed}{Colors.ENDC}")
        
        if failed > 0:
            print(f"\n{Colors.BOLD}Failed by Severity:{Colors.ENDC}")
            if critical > 0:
                print(f"  {Colors.FAIL}🔴 Critical: {critical}{Colors.ENDC}")
            if high > 0:
                print(f"  {Colors.WARNING}🟠 High: {high}{Colors.ENDC}")
            if medium > 0:
                print(f"  {Colors.WARNING}🟡 Medium: {medium}{Colors.ENDC}")
        
        if self.fixes_applied:
            print(f"\n{Colors.BOLD}{Colors.OKGREEN}Fixes Applied:{Colors.ENDC}")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
        
        # Provide next steps
        print(f"\n{Colors.BOLD}📌 Next Steps:{Colors.ENDC}")
        
        failed_critical = [r for r in self.results if not r.passed and r.severity == "critical"]
        if failed_critical:
            print(f"\n{Colors.FAIL}🚨 CRITICAL ISSUES FOUND:{Colors.ENDC}")
            for result in failed_critical:
                print(f"  ❌ {result.check_name}")
                print(f"     {result.message}")
                
                if "API keys" in result.check_name:
                    print(f"\n{Colors.WARNING}     Action Required:{Colors.ENDC}")
                    print(f"     1. Get API key from: https://openrouter.ai/keys")
                    print(f"     2. Open .env file")
                    print(f"     3. Add: OPENROUTER_API_KEY=sk-or-v1-your-key-here")
                    print(f"     4. Save and restart application")
        
        if passed == total:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ ALL CHECKS PASSED!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Your system is configured correctly.{Colors.ENDC}")
            print(f"{Colors.OKGREEN}نظامك مُكون بشكل صحيح.{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠️  Some issues need attention.{Colors.ENDC}")
            print(f"{Colors.WARNING}بعض المشاكل تحتاج إلى اهتمام.{Colors.ENDC}")
    
    def save_report(self, filename: str = "diagnostic_report.txt"):
        """Save diagnostic report to file"""
        report_path = self.project_root / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CogniForge Auto-Diagnostic Report\n")
            f.write("تقرير التشخيص التلقائي\n")
            f.write("="*80 + "\n\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Project Root: {self.project_root}\n\n")
            
            f.write("Diagnostic Results:\n")
            f.write("-"*80 + "\n\n")
            
            for result in self.results:
                status = "PASS" if result.passed else "FAIL"
                f.write(f"[{status}] {result.check_name}\n")
                f.write(f"  {result.message}\n")
                if not result.passed:
                    f.write(f"  Severity: {result.severity}\n")
                    f.write(f"  Fix Available: {result.fix_available}\n")
                f.write("\n")
            
            f.write("\nSummary:\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Checks: {len(self.results)}\n")
            f.write(f"Passed: {sum(1 for r in self.results if r.passed)}\n")
            f.write(f"Failed: {sum(1 for r in self.results if not r.passed)}\n")
            
            if self.fixes_applied:
                f.write("\nFixes Applied:\n")
                f.write("-"*80 + "\n")
                for fix in self.fixes_applied:
                    f.write(f"- {fix}\n")
        
        print(f"\n{Colors.OKGREEN}📄 Report saved to: {report_path}{Colors.ENDC}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CogniForge Auto-Diagnostic & Self-Healing System')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically apply fixes')
    parser.add_argument('--report', action='store_true', help='Save report to file')
    parser.add_argument('--report-file', default='diagnostic_report.txt', help='Report filename')
    
    args = parser.parse_args()
    
    diagnostic = CogniForgeAutoDiagnostic(auto_fix=args.auto_fix)
    diagnostic.run_diagnostics()
    diagnostic.print_summary()
    
    if args.report:
        diagnostic.save_report(args.report_file)
    
    # Return exit code based on critical failures
    critical_failures = sum(1 for r in diagnostic.results 
                          if not r.passed and r.severity == "critical")
    
    return 1 if critical_failures > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
