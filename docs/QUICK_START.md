# 🎯 Quick Start Guide - AI Microservices Platform

## TL;DR - Get Running in 10 Minutes

This guide gets you from zero to a running AI microservices platform as quickly as possible.

## Prerequisites (5 minutes)

```bash
# Install required tools
brew install kubectl helm istioctl  # macOS
# OR
sudo snap install kubectl helm --classic  # Linux

# Verify Kubernetes cluster access
kubectl cluster-info
kubectl get nodes
```

## Option 1: Local Development with Minikube (Recommended for Testing)

```bash
# 1. Start Minikube with enough resources
minikube start --cpus=4 --memory=8192 --disk-size=50g

# 2. Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server

# 3. Clone repository
git clone https://github.com/HOUSSAM16ai/my_ai_project
cd my_ai_project

# 4. Deploy everything
kubectl apply -k infra/k8s/

# 5. Wait for pods to be ready (3-5 minutes)
kubectl wait --for=condition=Ready pod -l app=router-service -n ai-services --timeout=300s

# 6. Test the services
minikube service router-service -n ai-services
```

## Option 2: Cloud Deployment (Production-Ready)

### AWS EKS
```bash
# 1. Create EKS cluster
eksctl create cluster \
  --name cogniforge-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed

# 2. Configure kubectl
aws eks update-kubeconfig --name cogniforge-prod --region us-east-1

# 3. Deploy the stack
./deploy.sh
```

### GCP GKE
```bash
# 1. Create GKE cluster
gcloud container clusters create cogniforge-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10

# 2. Configure kubectl
gcloud container clusters get-credentials cogniforge-prod --zone us-central1-a

# 3. Deploy
./deploy.sh
```

### Azure AKS
```bash
# 1. Create AKS cluster
az aks create \
  --resource-group cogniforge-rg \
  --name cogniforge-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10

# 2. Configure kubectl
az aks get-credentials --resource-group cogniforge-rg --name cogniforge-prod

# 3. Deploy
./deploy.sh
```

## Automated Deployment Script

Save this as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying CogniForge AI Microservices Platform..."

# Create namespaces
echo "📦 Creating namespaces..."
kubectl create namespace ai-services --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace infrastructure --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -

# Label for Istio injection
kubectl label namespace ai-services istio-injection=enabled --overwrite

# Install Istio (if not already installed)
if ! kubectl get namespace istio-system &> /dev/null; then
    echo "🔧 Installing Istio..."
    istioctl install --set profile=production -y
fi

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
kubectl apply -f infra/k8s/otel/collector-deployment.yaml
kubectl apply -f infra/k8s/mesh/istio-config.yaml

# Deploy AI services
echo "🤖 Deploying AI services..."
kubectl apply -f apps/router-service/k8s/deployment.yaml

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=Ready pod -l app=router-service -n ai-services --timeout=300s

# Get service URL
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
kubectl get pods -n ai-services
echo ""
echo "🌐 Access URLs:"
if command -v minikube &> /dev/null; then
    minikube service list
else
    kubectl get svc -n ai-services
fi
```

Make it executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Quick Test

```bash
# Get service URL
SERVICE_URL=$(kubectl get svc router-service -n ai-services -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test AI Router
curl -X POST http://$SERVICE_URL:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "routing_strategy": "balanced"
  }'

# Test Health
curl http://$SERVICE_URL:8000/health
```

## Access Dashboards

### Port Forwarding (Development)
```bash
# Grafana
kubectl port-forward -n observability svc/prometheus-grafana 3000:80

# Prometheus
kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090

# Jaeger
kubectl port-forward -n observability svc/jaeger-query 16686:16686
```

Then access:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686

## Troubleshooting

### Pods not starting?
```bash
# Check pod status
kubectl get pods -n ai-services

# View logs
kubectl logs -f deployment/router-service -n ai-services

# Describe pod
kubectl describe pod -l app=router-service -n ai-services
```

### Service not accessible?
```bash
# Check service
kubectl get svc -n ai-services

# Check endpoints
kubectl get endpoints router-service -n ai-services

# Check Istio sidecar
kubectl logs -l app=router-service -n ai-services -c istio-proxy
```

### Out of resources?
```bash
# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n ai-services

# Scale down if needed
kubectl scale deployment router-service --replicas=1 -n ai-services
```

## Next Steps

1. **Configure Monitoring**: Set up Prometheus + Grafana
2. **Add TLS**: Configure cert-manager and certificates
3. **Scale Up**: Increase replicas for production load
4. **Add Models**: Deploy your own models to KServe
5. **Enable GitOps**: Set up Argo CD for automated deployments

## Full Documentation

- [Complete Platform Documentation](MICROSERVICES_PLATFORM.md)
- [Detailed Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Implementation Summary](MICROSERVICES_IMPLEMENTATION.md)

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/HOUSSAM16ai/my_ai_project/issues)
- 💬 [Discussions](https://github.com/HOUSSAM16ai/my_ai_project/discussions)

---

**You're now running a world-class AI microservices platform! 🎉**
