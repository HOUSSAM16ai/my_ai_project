#!/bin/bash
# ======================================================================================
# GitLab CI/CD Pipeline Validation Script
# ======================================================================================
# Validate .gitlab-ci.yml before pushing

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔍 Validating GitLab CI/CD Pipeline${NC}"
echo ""

# Check if gitlab-ci.yml exists
if [[ ! -f ".gitlab-ci.yml" ]]; then
    echo -e "${RED}❌ .gitlab-ci.yml not found${NC}"
    exit 1
fi

# Validate YAML syntax
echo -e "${YELLOW}📋 Validating YAML syntax...${NC}"
if command -v yamllint &> /dev/null; then
    if yamllint -d '{extends: default, rules: {line-length: {max: 120}}}' .gitlab-ci.yml; then
        echo -e "${GREEN}✅ YAML syntax is valid${NC}"
    else
        echo -e "${RED}❌ YAML syntax errors found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  yamllint not installed, skipping syntax check${NC}"
fi

# Check for required stages
echo -e "${YELLOW}🔍 Checking required stages...${NC}"
REQUIRED_STAGES=("validate" "build" "test" "security" "quality" "deploy")
for stage in "${REQUIRED_STAGES[@]}"; do
    if grep -q "stage: ${stage}" .gitlab-ci.yml; then
        echo -e "${GREEN}   ✅ ${stage}${NC}"
    else
        echo -e "${RED}   ❌ ${stage} stage missing${NC}"
        exit 1
    fi
done

# Check for security scanning
echo -e "${YELLOW}🔒 Checking security scanning...${NC}"
SECURITY_CHECKS=("sast" "dependency" "container" "secret")
for check in "${SECURITY_CHECKS[@]}"; do
    if grep -q "${check}" .gitlab-ci.yml; then
        echo -e "${GREEN}   ✅ ${check}${NC}"
    else
        echo -e "${YELLOW}   ⚠️  ${check} not found${NC}"
    fi
done

# Check for caching
echo -e "${YELLOW}💾 Checking cache configuration...${NC}"
if grep -q "cache:" .gitlab-ci.yml; then
    echo -e "${GREEN}✅ Cache configured${NC}"
else
    echo -e "${YELLOW}⚠️  No cache configuration found${NC}"
fi

# Check for artifacts
echo -e "${YELLOW}📦 Checking artifacts configuration...${NC}"
if grep -q "artifacts:" .gitlab-ci.yml; then
    echo -e "${GREEN}✅ Artifacts configured${NC}"
else
    echo -e "${YELLOW}⚠️  No artifacts configuration found${NC}"
fi

# Validate with GitLab CI Lint (if available)
echo -e "${YELLOW}🔍 Validating with GitLab CI Lint...${NC}"
if command -v gitlab-ci-lint &> /dev/null; then
    if gitlab-ci-lint .gitlab-ci.yml; then
        echo -e "${GREEN}✅ Pipeline configuration is valid${NC}"
    else
        echo -e "${RED}❌ Pipeline configuration has errors${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  gitlab-ci-lint not available${NC}"
    echo "   Install: npm install -g gitlab-ci-lint"
fi

echo ""
echo -e "${GREEN}✅ Pipeline validation completed successfully!${NC}"
