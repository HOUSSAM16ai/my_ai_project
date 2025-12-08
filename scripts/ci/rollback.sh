#!/bin/bash
# ======================================================================================
# GitLab CI/CD Rollback Script
# ======================================================================================
# Automated rollback script for failed deployments

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-development}"
NAMESPACE="${ENVIRONMENT}"
REVISION="${2:-0}"  # 0 means previous revision

echo -e "${YELLOW}⏪ Starting rollback in ${ENVIRONMENT}${NC}"
echo "   Namespace: ${NAMESPACE}"
echo "   Revision: ${REVISION}"
echo ""

# Check kubectl connection
if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Show rollout history
echo -e "${YELLOW}📜 Rollout history:${NC}"
kubectl rollout history deployment/cogniforge -n "${NAMESPACE}"

# Perform rollback
if [[ "${REVISION}" == "0" ]]; then
    echo -e "${YELLOW}⏪ Rolling back to previous revision...${NC}"
    kubectl rollout undo deployment/cogniforge -n "${NAMESPACE}"
else
    echo -e "${YELLOW}⏪ Rolling back to revision ${REVISION}...${NC}"
    kubectl rollout undo deployment/cogniforge -n "${NAMESPACE}" --to-revision="${REVISION}"
fi

# Wait for rollback
echo -e "${YELLOW}⏳ Waiting for rollback to complete...${NC}"
kubectl rollout status deployment/cogniforge -n "${NAMESPACE}" --timeout=10m

# Verify rollback
READY_REPLICAS=$(kubectl get deployment cogniforge -n "${NAMESPACE}" -o jsonpath='{.status.readyReplicas}')
DESIRED_REPLICAS=$(kubectl get deployment cogniforge -n "${NAMESPACE}" -o jsonpath='{.spec.replicas}')

if [[ "${READY_REPLICAS}" == "${DESIRED_REPLICAS}" ]]; then
    echo -e "${GREEN}✅ Rollback successful!${NC}"
    echo "   Ready replicas: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
else
    echo -e "${RED}❌ Rollback failed!${NC}"
    echo "   Ready replicas: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
    exit 1
fi

# Show current status
echo -e "${YELLOW}📊 Current status:${NC}"
kubectl get pods -n "${NAMESPACE}" -l app=cogniforge

echo ""
echo -e "${GREEN}✅ Rollback completed successfully!${NC}"
