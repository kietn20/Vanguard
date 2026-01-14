#!/bin/bash
set -e

echo "========================================="
echo "🏭 Vanguard Quick Start"
echo "========================================="
echo ""

# Check prerequisites
command -v minikube >/dev/null 2>&1 || { echo "❌ minikube not found. Install from: https://minikube.sigs.k8s.io/"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found. Install from: https://kubernetes.io/docs/tasks/tools/"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker not found. Install Docker Desktop."; exit 1; }

echo "✅ Prerequisites check passed"
echo ""

# Start Minikube if not running
if ! minikube status >/dev/null 2>&1; then
    echo "🚀 Starting Minikube..."
    minikube start --memory=8192 --cpus=4
else
    echo "✅ Minikube is already running"
fi

echo ""
echo "📦 Building Docker images..."
cd "$(dirname "$0")/../.."
./infrastructure/scripts/build-images.sh

echo ""
echo "🚀 Deploying to Kubernetes..."
./infrastructure/scripts/deploy.sh

echo ""
echo "⏳ Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod --all -n vanguard --timeout=300s

echo ""
echo "========================================="
echo "🎉 Vanguard is now running!"
echo "========================================="
echo ""
echo "📊 View dashboards:"
echo "   kubectl port-forward -n vanguard svc/grafana-service 3000:3000"
echo "   Open: http://localhost:3000 (admin/vanguard2024)"
echo ""
echo "🤖 View agent logs:"
echo "   kubectl logs -f deployment/ai-agents -n vanguard"
echo ""
echo "🔍 Check status:"
echo "   kubectl get pods -n vanguard"
