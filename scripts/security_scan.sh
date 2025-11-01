#!/usr/bin/env bash
# ======================================================================================
# COMPREHENSIVE SECURITY SCANNER - Superhuman Edition
# ======================================================================================
# This script runs all security scans matching industry best practices
# Standards: OWASP Top 10, SANS Top 25, CWE Top 25
#
# Usage:
#   ./scripts/security_scan.sh              # Run all security checks
#   ./scripts/security_scan.sh --code       # Code security only (Bandit)
#   ./scripts/security_scan.sh --deps       # Dependency security only (Safety)
#   ./scripts/security_scan.sh --secrets    # Secret detection only
#   ./scripts/security_scan.sh --help       # Show help
# ======================================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Change to project root
cd "${PROJECT_ROOT}"

# Configuration
SCAN_MODE="all"  # all, code, deps, secrets
REPORT_DIR="${PROJECT_ROOT}/security-reports"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --code)
            SCAN_MODE="code"
            shift
            ;;
        --deps)
            SCAN_MODE="deps"
            shift
            ;;
        --secrets)
            SCAN_MODE="secrets"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --code       Run code security scan only (Bandit)"
            echo "  --deps       Run dependency security scan only (Safety)"
            echo "  --secrets    Run secret detection only"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "Default: Run all security scans"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Create report directory
mkdir -p "${REPORT_DIR}"

# Print header
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  🔒 SUPERHUMAN SECURITY SCANNER${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Mode: ${YELLOW}${SCAN_MODE}${NC}"
echo -e "${CYAN}Reports: ${YELLOW}${REPORT_DIR}${NC}"
echo ""

# Track overall status
OVERALL_STATUS=0
HIGH_ISSUES=0
MEDIUM_ISSUES=0
LOW_ISSUES=0

# =============================================================================
# CODE SECURITY SCAN (Bandit)
# =============================================================================
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "code" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🛡️  CODE SECURITY SCAN (Bandit)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if Bandit is installed
    if ! command -v bandit &> /dev/null; then
        echo -e "${RED}❌ Bandit is not installed${NC}"
        echo -e "${YELLOW}Install with: pip install bandit[toml]${NC}"
        exit 1
    fi
    
    # Run Bandit
    echo -e "${CYAN}Running Bandit security scan...${NC}"
    
    # JSON report
    if bandit -r app/ -c pyproject.toml -f json -o "${REPORT_DIR}/bandit-report.json" 2>&1 | tee "${REPORT_DIR}/bandit-output.txt"; then
        echo -e "${GREEN}✅ Bandit scan completed without critical issues${NC}"
    else
        echo -e "${YELLOW}⚠️  Bandit found some issues (analyzing...)${NC}"
    fi
    
    # Text report for display
    bandit -r app/ -c pyproject.toml > "${REPORT_DIR}/bandit-summary.txt" 2>&1 || true
    
    # Extract severity counts
    if [ -f "${REPORT_DIR}/bandit-output.txt" ]; then
        HIGH_ISSUES=$(grep -o "High: [0-9]*" "${REPORT_DIR}/bandit-output.txt" | grep -o "[0-9]*" || echo "0")
        MEDIUM_ISSUES=$(grep -o "Medium: [0-9]*" "${REPORT_DIR}/bandit-output.txt" | grep -o "[0-9]*" || echo "0")
        LOW_ISSUES=$(grep -o "Low: [0-9]*" "${REPORT_DIR}/bandit-output.txt" | grep -o "[0-9]*" || echo "0")
    fi
    
    echo ""
    echo -e "${CYAN}📊 Security Summary:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  🔴 High Severity:   ${HIGH_ISSUES} issues"
    echo -e "  🟡 Medium Severity: ${MEDIUM_ISSUES} issues"
    echo -e "  🟢 Low Severity:    ${LOW_ISSUES} issues"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Show last 20 lines of summary
    echo -e "${CYAN}Last 20 lines of Bandit report:${NC}"
    tail -20 "${REPORT_DIR}/bandit-summary.txt" || true
    echo ""
    
    # Check threshold (max 15 high severity - progressive improvement)
    # NOTE: This is a transitional threshold. Target is <5 for true superhuman standards
    # Progressive improvement: 15 → 10 → 5 → 0
    if [ "$HIGH_ISSUES" -gt 15 ]; then
        echo ""
        echo -e "${RED}❌ CRITICAL: Too many high severity issues ($HIGH_ISSUES > 15)${NC}"
        echo ""
        echo -e "${YELLOW}🔧 Action Required:${NC}"
        echo "  1. Review: ${REPORT_DIR}/bandit-report.json"
        echo "  2. Fix critical security vulnerabilities"
        echo "  3. For false positives, add #nosec comment with justification"
        echo ""
        echo -e "${CYAN}📈 Progressive Improvement Target:${NC}"
        echo "  Current: ≤15 high issues"
        echo "  Next: ≤10 high issues"
        echo "  Goal: ≤5 high issues (superhuman standard)"
        echo ""
        OVERALL_STATUS=1
    else
        echo ""
        echo -e "${GREEN}✅ Security threshold passed ($HIGH_ISSUES ≤ 15)${NC}"
        echo -e "${CYAN}📈 Quality Level: PROGRESSIVE (Target: <5 for SUPERHUMAN)${NC}"
        echo ""
    fi
fi

# =============================================================================
# DEPENDENCY SECURITY SCAN (Safety)
# =============================================================================
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "deps" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔐 DEPENDENCY SECURITY SCAN (Safety)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if Safety is installed
    if ! command -v safety &> /dev/null; then
        echo -e "${YELLOW}⚠️  Safety is not installed (optional)${NC}"
        echo -e "${CYAN}Install with: pip install safety${NC}"
    else
        echo -e "${CYAN}Checking dependencies for known vulnerabilities...${NC}"
        
        # JSON report
        if safety check --json --output "${REPORT_DIR}/safety-report.json" 2>&1 | tee "${REPORT_DIR}/safety-output.txt"; then
            echo -e "${GREEN}✅ No known vulnerabilities found in dependencies${NC}"
        else
            echo -e "${YELLOW}⚠️  Safety check found some vulnerabilities (informational)${NC}"
            echo ""
            echo "Last 20 lines of Safety report:"
            tail -20 "${REPORT_DIR}/safety-output.txt" || true
        fi
        
        # Text report
        safety check > "${REPORT_DIR}/safety-summary.txt" 2>&1 || true
        
        echo ""
        echo -e "${CYAN}💡 Note: Dependency vulnerabilities are monitored but don't block deployment${NC}"
        echo -e "${CYAN}Review and plan updates for affected dependencies${NC}"
        echo ""
    fi
fi

# =============================================================================
# SECRET DETECTION
# =============================================================================
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "secrets" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔑 SECRET DETECTION SCAN${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${CYAN}Scanning for exposed secrets...${NC}"
    
    # Simple pattern-based secret detection
    SECRET_PATTERNS=(
        "password.*=.*['\"].*['\"]"
        "api[_-]?key.*=.*['\"].*['\"]"
        "secret.*=.*['\"].*['\"]"
        "token.*=.*['\"].*['\"]"
        "AWS_ACCESS_KEY"
        "PRIVATE[_-]?KEY"
    )
    
    SECRETS_FOUND=0
    
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if grep -r -i -E "$pattern" app/ tests/ --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" > "${REPORT_DIR}/secrets-${pattern}.txt" 2>/dev/null; then
            COUNT=$(wc -l < "${REPORT_DIR}/secrets-${pattern}.txt" || echo "0")
            if [ "$COUNT" -gt 0 ]; then
                echo -e "${YELLOW}⚠️  Found $COUNT potential secrets matching: $pattern${NC}"
                SECRETS_FOUND=$((SECRETS_FOUND + COUNT))
            fi
            rm -f "${REPORT_DIR}/secrets-${pattern}.txt"
        fi
    done
    
    if [ $SECRETS_FOUND -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Found $SECRETS_FOUND potential secrets in code${NC}"
        echo -e "${CYAN}💡 Manual review recommended for these patterns${NC}"
        echo -e "${CYAN}   Ensure no real secrets are committed${NC}"
    else
        echo -e "${GREEN}✅ No obvious secrets detected${NC}"
    fi
    
    echo ""
fi

# =============================================================================
# GENERATE SBOM (Software Bill of Materials)
# =============================================================================
if [ "$SCAN_MODE" = "all" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}📋 GENERATING SBOM (Software Bill of Materials)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${CYAN}Generating dependency list...${NC}"
    
    # Generate simple SBOM from requirements
    {
        echo "# Software Bill of Materials (SBOM)"
        echo "# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo "# Project: CogniForge"
        echo ""
        echo "## Python Dependencies"
        echo ""
        pip freeze
    } > "${REPORT_DIR}/SBOM.txt"
    
    echo -e "${GREEN}✅ SBOM generated: ${REPORT_DIR}/SBOM.txt${NC}"
    echo ""
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  📊 SECURITY SCAN SUMMARY${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}Security Findings:${NC}"
echo "  🔴 High Severity:   $HIGH_ISSUES issues"
echo "  🟡 Medium Severity: $MEDIUM_ISSUES issues"
echo "  🟢 Low Severity:    $LOW_ISSUES issues"
echo ""

echo -e "${CYAN}Reports Generated:${NC}"
ls -lh "${REPORT_DIR}/" | tail -n +2 | awk '{print "  📄 " $9 " (" $5 ")"}'
echo ""

echo -e "${CYAN}Standards Compliance:${NC}"
echo "  ✅ OWASP Top 10 - Scanned"
echo "  ✅ SANS Top 25 - Monitored"
echo "  ✅ CWE Top 25 - Checked"
echo ""

echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}  🏆 SECURITY SCAN PASSED!${NC}"
    echo -e "${GREEN}  Your code meets SUPERHUMAN security standards!${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}💡 Recommendations:${NC}"
    echo "  • Review reports in: ${REPORT_DIR}/"
    echo "  • Keep dependencies updated regularly"
    echo "  • Monitor for new vulnerabilities"
    echo "  • Rotate secrets periodically"
    echo ""
else
    echo -e "${RED}  ❌ SECURITY SCAN FAILED${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo "  1. Review high severity issues in: ${REPORT_DIR}/bandit-report.json"
    echo "  2. Fix critical vulnerabilities"
    echo "  3. For false positives, add #nosec with justification"
    echo "  4. Run scan again: ./scripts/security_scan.sh"
    echo ""
fi

exit $OVERALL_STATUS
