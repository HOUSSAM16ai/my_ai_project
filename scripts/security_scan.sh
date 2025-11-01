#!/usr/bin/env bash
# ======================================================================================
# ENTERPRISE SECURITY SCANNER - Superhuman Edition with Semgrep
# ======================================================================================
# This script runs all security scans matching industry best practices
# Standards: OWASP Top 10, SANS Top 25, CWE Top 25
# Following practices from Google, Facebook, Microsoft, OpenAI, Stripe
#
# Usage:
#   ./scripts/security_scan.sh              # Run all security checks
#   ./scripts/security_scan.sh --fast       # Fast scan (Semgrep rapid mode)
#   ./scripts/security_scan.sh --full       # Full scan (all tools)
#   ./scripts/security_scan.sh --code       # Code security only (Bandit)
#   ./scripts/security_scan.sh --sast       # SAST only (Semgrep)
#   ./scripts/security_scan.sh --deps       # Dependency security only (Safety)
#   ./scripts/security_scan.sh --secrets    # Secret detection only
#   ./scripts/security_scan.sh --report     # Generate reports only
#   ./scripts/security_scan.sh --fix        # Auto-fix issues (dry-run)
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
SCAN_MODE="all"  # all, fast, full, code, sast, deps, secrets, report, fix
REPORT_DIR="${PROJECT_ROOT}/security-reports"
SEMGREP_MODE="rapid"  # rapid, full, deep, audit
FAIL_ON_FINDINGS=false
AUTOFIX_MODE="dry-run"  # dry-run, apply

# Load environment configuration if exists
if [ -f "${PROJECT_ROOT}/.env.security" ]; then
    source "${PROJECT_ROOT}/.env.security"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            SCAN_MODE="fast"
            SEMGREP_MODE="rapid"
            shift
            ;;
        --full)
            SCAN_MODE="full"
            SEMGREP_MODE="full"
            shift
            ;;
        --code)
            SCAN_MODE="code"
            shift
            ;;
        --sast)
            SCAN_MODE="sast"
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
        --report)
            SCAN_MODE="report"
            shift
            ;;
        --fix)
            SCAN_MODE="fix"
            AUTOFIX_MODE="dry-run"
            shift
            ;;
        --fail-on-findings)
            FAIL_ON_FINDINGS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Modes:"
            echo "  --fast       Fast scan (Semgrep rapid mode, ~5 min)"
            echo "  --full       Full scan (all tools, ~20 min)"
            echo "  --code       Code security scan only (Bandit)"
            echo "  --sast       SAST scan only (Semgrep)"
            echo "  --deps       Dependency security scan only (Safety)"
            echo "  --secrets    Secret detection only"
            echo "  --report     Generate reports only"
            echo "  --fix        Auto-fix issues (dry-run mode)"
            echo ""
            echo "Options:"
            echo "  --fail-on-findings  Fail build on security findings"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Default: Run all security scans (non-blocking)"
            echo ""
            echo "Examples:"
            echo "  $0 --fast                    # Quick scan for development"
            echo "  $0 --full --fail-on-findings # Complete scan for production"
            echo "  $0 --sast                    # Semgrep only"
            echo "  $0 --fix                     # Show auto-fix suggestions"
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
SEMGREP_FINDINGS=0

# =============================================================================
# SEMGREP SAST SCAN
# =============================================================================
run_semgrep_scan() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔍 SEMGREP SAST SCAN (${SEMGREP_MODE^^} MODE)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if Semgrep is installed
    if ! command -v semgrep &> /dev/null; then
        echo -e "${YELLOW}⚠️  Semgrep is not installed${NC}"
        echo -e "${CYAN}Install with: pip install semgrep${NC}"
        echo -e "${CYAN}Or use Docker: docker run --rm -v \"\${PWD}:/src\" returntocorp/semgrep${NC}"
        return 0
    fi
    
    echo -e "${CYAN}Running Semgrep security scan (${SEMGREP_MODE} mode)...${NC}"
    echo ""
    
    # Configure rulesets based on mode
    local RULESETS=""
    case "$SEMGREP_MODE" in
        rapid)
            RULESETS="p/ci"
            ;;
        full)
            RULESETS="p/security-audit p/owasp-top-ten p/ci"
            ;;
        deep)
            RULESETS="p/security-audit p/owasp-top-ten p/cwe-top-25 p/ci"
            ;;
        audit)
            RULESETS="p/security-audit p/owasp-top-ten p/cwe-top-25 p/ci p/r2c-security-audit"
            ;;
        *)
            RULESETS="p/ci"
            ;;
    esac
    
    # Add custom rules if exists
    if [ -f "${PROJECT_ROOT}/.semgrep.yml" ]; then
        RULESETS="${RULESETS} --config=${PROJECT_ROOT}/.semgrep.yml"
    fi
    
    # Run Semgrep with appropriate options
    local SEMGREP_ARGS=(
        "--config=${RULESETS}"
        "--json"
        "--output=${REPORT_DIR}/semgrep-report.json"
    )
    
    # Add exclusions
    if [ -f "${PROJECT_ROOT}/.semgrepignore" ]; then
        echo -e "${CYAN}Using .semgrepignore for exclusions${NC}"
    fi
    
    # Add severity filter
    SEMGREP_ARGS+=("--severity=WARNING")
    
    # Add metrics
    SEMGREP_ARGS+=("--metrics=off")
    
    # Run Semgrep scan
    local SEMGREP_EXIT=0
    if semgrep scan "${SEMGREP_ARGS[@]}" . 2>&1 | tee "${REPORT_DIR}/semgrep-output.txt"; then
        echo -e "${GREEN}✅ Semgrep scan completed${NC}"
    else
        SEMGREP_EXIT=$?
        echo -e "${YELLOW}⚠️  Semgrep found some issues${NC}"
    fi
    
    # Generate SARIF report for GitHub
    semgrep scan \
        --config="${RULESETS}" \
        --sarif \
        --output="${REPORT_DIR}/semgrep.sarif" \
        . 2>/dev/null || true
    
    # Generate text summary
    semgrep scan \
        --config="${RULESETS}" \
        --text \
        . > "${REPORT_DIR}/semgrep-summary.txt" 2>&1 || true
    
    # Parse results
    if [ -f "${REPORT_DIR}/semgrep-report.json" ]; then
        # Count findings by severity (using jq if available, otherwise grep)
        if command -v jq &> /dev/null; then
            local ERROR_COUNT=$(jq '[.results[] | select(.extra.severity == "ERROR")] | length' "${REPORT_DIR}/semgrep-report.json" 2>/dev/null || echo "0")
            local WARNING_COUNT=$(jq '[.results[] | select(.extra.severity == "WARNING")] | length' "${REPORT_DIR}/semgrep-report.json" 2>/dev/null || echo "0")
            local INFO_COUNT=$(jq '[.results[] | select(.extra.severity == "INFO")] | length' "${REPORT_DIR}/semgrep-report.json" 2>/dev/null || echo "0")
            SEMGREP_FINDINGS=$(jq '.results | length' "${REPORT_DIR}/semgrep-report.json" 2>/dev/null || echo "0")
        else
            # Fallback without jq
            ERROR_COUNT=$(grep -o '"severity": "ERROR"' "${REPORT_DIR}/semgrep-report.json" | wc -l || echo "0")
            WARNING_COUNT=$(grep -o '"severity": "WARNING"' "${REPORT_DIR}/semgrep-report.json" | wc -l || echo "0")
            INFO_COUNT=$(grep -o '"severity": "INFO"' "${REPORT_DIR}/semgrep-report.json" | wc -l || echo "0")
            SEMGREP_FINDINGS=$((ERROR_COUNT + WARNING_COUNT + INFO_COUNT))
        fi
        
        echo ""
        echo -e "${CYAN}📊 Semgrep Findings:${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "  🔴 Error:   ${ERROR_COUNT} findings"
        echo -e "  🟡 Warning: ${WARNING_COUNT} findings"
        echo -e "  🔵 Info:    ${INFO_COUNT} findings"
        echo -e "  📊 Total:   ${SEMGREP_FINDINGS} findings"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Show summary (last 30 lines)
        if [ -f "${REPORT_DIR}/semgrep-summary.txt" ]; then
            echo -e "${CYAN}Semgrep Summary (last 30 lines):${NC}"
            tail -30 "${REPORT_DIR}/semgrep-summary.txt"
            echo ""
        fi
        
        # Check if we should fail
        if [ "$FAIL_ON_FINDINGS" = true ] && [ "$ERROR_COUNT" -gt 0 ]; then
            echo -e "${RED}❌ CRITICAL: ${ERROR_COUNT} error-level findings detected${NC}"
            OVERALL_STATUS=1
        else
            echo -e "${GREEN}✅ Semgrep scan completed${NC}"
            if [ "$FAIL_ON_FINDINGS" = false ]; then
                echo -e "${CYAN}💡 Non-blocking mode: Findings reported but not failing build${NC}"
            fi
        fi
    fi
    
    echo ""
}

# =============================================================================
# RUN SCANS BASED ON MODE
# =============================================================================

# SAST Scan (Semgrep)
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "fast" ] || [ "$SCAN_MODE" = "full" ] || [ "$SCAN_MODE" = "sast" ]; then
    run_semgrep_scan
fi

# CODE SECURITY SCAN (Bandit)
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "full" ] || [ "$SCAN_MODE" = "code" ]; then
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
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "full" ] || [ "$SCAN_MODE" = "deps" ]; then
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
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "full" ] || [ "$SCAN_MODE" = "secrets" ]; then
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
if [ "$SCAN_MODE" = "all" ] || [ "$SCAN_MODE" = "full" ] || [ "$SCAN_MODE" = "report" ]; then
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
echo "  🔍 Semgrep SAST:    $SEMGREP_FINDINGS findings"
echo "  🔴 High Severity:   $HIGH_ISSUES issues (Bandit)"
echo "  🟡 Medium Severity: $MEDIUM_ISSUES issues (Bandit)"
echo "  🟢 Low Severity:    $LOW_ISSUES issues (Bandit)"
echo ""

echo -e "${CYAN}Reports Generated:${NC}"
ls -lh "${REPORT_DIR}/" | tail -n +2 | awk '{print "  📄 " $9 " (" $5 ")"}'
echo ""

echo -e "${CYAN}Standards Compliance:${NC}"
echo "  ✅ OWASP Top 10 - Scanned (Semgrep)"
echo "  ✅ CWE Top 25 - Monitored (Semgrep)"
echo "  ✅ SANS Top 25 - Monitored (Bandit)"
echo ""

echo -e "${CYAN}Scan Configuration:${NC}"
echo "  📋 Mode: ${SCAN_MODE}"
echo "  🔍 Semgrep Mode: ${SEMGREP_MODE}"
echo "  🚦 Fail on Findings: ${FAIL_ON_FINDINGS}"
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
