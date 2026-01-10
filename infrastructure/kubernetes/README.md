# Kubernetes Deployment Guide

## Prerequisites

### Required Tools
- **Docker** (for building images)
- **kubectl** (Kubernetes CLI)
- **Minikube** (for local testing) OR **AWS CLI** (for EKS)

### Installation
```bash
# macOS
brew install kubectl minikube docker

# Verify installations
kubectl version --client
minikube version
docker --version
```

---

## Local Deployment (Minikube)

### Quick Start
```bash
# From project root
cd infrastructure/scripts

# Build and deploy everything
./local-deploy.sh
```

This script will:
1. Start Minikube (if not running)
2. Build all Docker images
3. Deploy to Kubernetes
4. Wait for all pods to be ready

### Manual Steps
```bash
# Start Minikube
minikube start --memory=8192 --cpus=4

# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build images
./build-images.sh

# Deploy
./deploy.sh
```

---

## Verify Deployment
```bash
# Check all pods
kubectl get pods -n vanguard

# Check services
kubectl get svc -n vanguard

# Check StatefulSets
kubectl get statefulset -n vanguard

# View logs
kubectl logs -f deployment/ai-agents -n vanguard
kubectl logs -f deployment/inventory-service -n vanguard
kubectl logs -f statefulset/kafka -n vanguard
```

---

## Access Services

### Port Forwarding
```bash
# Inventory Service
kubectl port-forward -n vanguard svc/inventory-service 8082:8082

# Guardrail Service
kubectl port-forward -n vanguard svc/guardrail-service 8083:8083

# Maintenance Service
kubectl port-forward -n vanguard svc/maintenance-service 8081:8081

# PostgreSQL
kubectl port-forward -n vanguard svc/postgres-service 5432:5432

# Kafka
kubectl port-forward -n vanguard svc/kafka-service 9092:9092
```

Then access:
- Inventory API: http://localhost:8082/api/inventory/parts
- Guardrail API: http://localhost:8083/api/guardrail/health
- Audit Logs: http://localhost:8083/api/guardrail/audit/stats

---

## Scaling
```bash
# Scale Inventory Service
kubectl scale deployment/inventory-service -n vanguard --replicas=3

# Scale AI Agents
kubectl scale deployment/ai-agents -n vanguard --replicas=2

# Check status
kubectl get pods -n vanguard -l app=inventory-service
```

---

## Troubleshooting

### Pod not starting
```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n vanguard

# Check logs
kubectl logs <pod-name> -n vanguard

# Check previous logs if crashed
kubectl logs <pod-name> -n vanguard --previous
```

### Service not accessible
```bash
# Check service endpoints
kubectl get endpoints -n vanguard

# Test from within cluster
kubectl run -it --rm debug --image=alpine --restart=Never -n vanguard -- sh
# Inside pod:
wget -qO- http://inventory-service:8082/api/inventory/parts
```

### Database connection issues
```bash
# Test PostgreSQL connection
kubectl exec -it statefulset/postgres -n vanguard -- psql -U vanguard -d vanguard

# Inside psql:
\dt  # List tables
SELECT * FROM parts LIMIT 5;
```

### Kafka issues
```bash
# Check Kafka logs
kubectl logs statefulset/kafka -n vanguard

# List topics
kubectl exec -it statefulset/kafka -n vanguard -- \
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Consume messages
kubectl exec -it statefulset/kafka -n vanguard -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic factory_events \
  --from-beginning
```

---

## Resource Management

### View Resource Usage
```bash
# Per pod
kubectl top pods -n vanguard

# Per node
kubectl top nodes

# Detailed resource requests/limits
kubectl describe nodes
```

### Adjust Resources

Edit deployment YAML files and update resource requests/limits, then:
```bash
kubectl apply -f <deployment-file>.yaml
```

---

## Clean Up

### Remove all resources
```bash
# Delete namespace (removes everything)
kubectl delete namespace vanguard

# Or delete individually
kubectl delete -f kubernetes/
```

### Stop Minikube
```bash
minikube stop
# Or completely remove
minikube delete
```

---

## Production Deployment (AWS EKS)

Coming in deployment documentation...

Key differences:
- Use ECR for Docker registry
- Configure EBS for persistent volumes
- Set up ingress controller
- Configure SSL/TLS
- Enable cluster autoscaling
- Set up monitoring with Prometheus/Grafana
