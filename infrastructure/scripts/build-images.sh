set -e

echo "========================================="
echo "Building Vanguard Docker Images"
echo "========================================="

# Change to project root
cd "$(dirname "$0")/../.."

# Build Java services
echo ""
echo "Building Inventory Service..."
cd services/inventory-service
docker build -t vanguard/inventory-service:latest .

echo ""
echo "Building Guardrail Service..."
cd ../guardrail-service
docker build -t vanguard/guardrail-service:latest .

echo ""
echo "Building Maintenance Service..."
cd ../maintenance-service
docker build -t vanguard/maintenance-service:latest .

# Build Python services
echo ""
echo "Building AI Agents..."
cd ../../brain
docker build -t vanguard/ai-agents:latest .

echo ""
echo "Building Simulator..."
cd ../simulator
docker build -t vanguard/simulator:latest .

echo ""
echo "========================================="
echo "All images built successfully!"
echo "========================================="
echo ""
echo "Images created:"
docker images | grep vanguard

echo ""
echo "To push to a registry, run:"
echo "  docker tag vanguard/inventory-service:latest YOUR_REGISTRY/vanguard/inventory-service:latest"
echo "  docker push YOUR_REGISTRY/vanguard/inventory-service:latest"
