#!/bin/bash
# ======================================================================================
# GitLab CI/CD Deployment Script
# ======================================================================================
# Automated deployment script for Kubernetes environments

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-development}"
IMAGE_TAG="${2:-latest}"
NAMESPACE="${ENVIRONMENT}"
KUSTOMIZE_DIR="infra/k8s/overlays/${ENVIRONMENT}"

echo -e "${GREEN}🚀 Starting deployment to ${ENVIRONMENT}${NC}"
echo "   Image: ${IMAGE_TAG}"
echo "   Namespace: ${NAMESPACE}"
echo ""

# Validate environment
if [[ ! -d "${KUSTOMIZE_DIR}" ]]; then
    echo -e "${RED}❌ Invalid environment: ${ENVIRONMENT}${NC}"
    echo "   Available: development, staging, production"
    exit 1
fi

# Check kubectl connection
echo -e "${YELLOW}🔍 Checking Kubernetes connection...${NC}"
if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connected to cluster${NC}"

# Create namespace if not exists
echo -e "${YELLOW}📦 Ensuring namespace exists...${NC}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Update image tag in kustomization
echo -e "${YELLOW}🏷️  Updating image tag...${NC}"
cd "${KUSTOMIZE_DIR}"
kustomize edit set image "CONTAINER_IMAGE_PLACEHOLDER=${CI_REGISTRY_IMAGE}:${IMAGE_TAG}"
cd -

# Preview changes
echo -e "${YELLOW}👀 Preview of changes:${NC}"
kubectl diff -k "${KUSTOMIZE_DIR}" || true

# Apply deployment
echo -e "${YELLOW}🚀 Applying deployment...${NC}"
kubectl apply -k "${KUSTOMIZE_DIR}"

# Wait for rollout
echo -e "${YELLOW}⏳ Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/cogniforge -n "${NAMESPACE}" --timeout=10m

# Verify deployment
echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
READY_REPLICAS=$(kubectl get deployment cogniforge -n "${NAMESPACE}" -o jsonpath='{.status.readyReplicas}')
DESIRED_REPLICAS=$(kubectl get deployment cogniforge -n "${NAMESPACE}" -o jsonpath='{.spec.replicas}')

if [[ "${READY_REPLICAS}" == "${DESIRED_REPLICAS}" ]]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo "   Ready replicas: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo "   Ready replicas: ${READY_REPLICAS}/${DESIRED_REPLICAS}"
    exit 1
fi

# Get service URL
echo -e "${YELLOW}🌐 Service information:${NC}"
kubectl get ingress -n "${NAMESPACE}"

# Show pod status
echo -e "${YELLOW}📊 Pod status:${NC}"
kubectl get pods -n "${NAMESPACE}" -l app=cogniforge

echo ""
echo -e "${GREEN}✅ Deployment to ${ENVIRONMENT} completed successfully!${NC}"
