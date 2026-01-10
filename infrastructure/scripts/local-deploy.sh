set -e

echo "========================================="
echo "Local Kubernetes Deployment (Minikube)"
echo "========================================="

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "Minikube not found. Install with:"
    echo "   brew install minikube"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl not found. Install with:"
    echo "   brew install kubectl"
    exit 1
fi

# Start minikube if not running
echo ""
echo "Checking Minikube status..."
if ! minikube status &> /dev/null; then
    echo "Starting Minikube..."
    minikube start --memory=8192 --cpus=4
else
    echo "Minikube is already running"
fi

# Use Minikube's Docker daemon
echo ""
echo "Configuring Docker to use Minikube's daemon..."
eval $(minikube docker-env)

# Build images
echo ""
echo "Building Docker images..."
cd "$(dirname "$0")"
./build-images.sh

# Deploy to Kubernetes
echo ""
echo "Deploying to Kubernetes..."
./deploy.sh

# Wait for all pods to be ready
echo ""
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod --all -n vanguard --timeout=300s

# Show status
echo ""
echo "========================================="
echo "Local deployment complete!"
echo "========================================="
echo ""
echo "Pod status:"
kubectl get pods -n vanguard
echo ""
echo "Services:"
kubectl get svc -n vanguard
echo ""
echo "To access services locally:"
echo "  kubectl port-forward -n vanguard svc/inventory-service 8082:8082"
echo "  kubectl port-forward -n vanguard svc/guardrail-service 8083:8083"
echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/ai-agents -n vanguard"
echo ""
echo "To open Kubernetes dashboard:"
echo "  minikube dashboard"
