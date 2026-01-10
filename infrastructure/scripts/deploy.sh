set -e

echo "========================================="
echo "Deploying Vanguard to Kubernetes"
echo "========================================="

# Change to k8s directory
cd "$(dirname "$0")/../kubernetes"

# Create namespace
echo ""
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Apply ConfigMap and Secrets
echo ""
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

echo ""
echo "Applying Secrets..."
kubectl apply -f secrets.yaml

# Deploy infrastructure
echo ""
echo "Deploying PostgreSQL..."
kubectl apply -f postgres-statefulset.yaml

echo ""
echo "Deploying Kafka..."
kubectl apply -f kafka-statefulset.yaml

# Wait for infrastructure to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n vanguard --timeout=120s

echo ""
echo "Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n vanguard --timeout=180s

# Deploy services
echo ""
echo "Deploying Guardrail Service..."
kubectl apply -f guardrail-deployment.yaml

echo ""
echo "Deploying Inventory Service..."
kubectl apply -f inventory-deployment.yaml

echo ""
echo "Deploying Maintenance Service..."
kubectl apply -f maintenance-deployment.yaml

# Deploy agents and simulator
echo ""
echo "Deploying AI Agents..."
kubectl apply -f agent-deployment.yaml

echo ""
echo "Deploying Simulator..."
kubectl apply -f simulator-deployment.yaml

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Check status with:"
echo "  kubectl get pods -n vanguard"
echo ""
echo "View logs with:"
echo "  kubectl logs -f deployment/inventory-service -n vanguard"
echo ""
echo "Access services with:"
echo "  kubectl port-forward -n vanguard svc/inventory-service 8082:8082"
