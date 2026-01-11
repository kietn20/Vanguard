# Vanguard Deployment Guide

## Architecture Overview

Vanguard is deployed as a cloud-native microservices architecture on Kubernetes with the following components:

### Services
- **Inventory Service** (2 replicas): Manages spare parts inventory
- **Guardrail Service** (2 replicas): Safety validation for AI decisions
- **Maintenance Service** (1 replica): Processes maintenance events
- **AI Agents** (1 replica): Intelligent event processing
- **Simulator** (1 replica): Generates factory events

### Infrastructure
- **Kafka** (StatefulSet): Event streaming platform
- **PostgreSQL** (StatefulSet): Persistent data storage

---

## Quick Start

### Local Development (Minikube)
```bash
# 1. Start Minikube
minikube start --memory=8192 --cpus=4

# 2. Use Minikube's Docker
eval $(minikube docker-env)

# 3. Build images
cd ~/projects/vanguard
./infrastructure/scripts/build-images.sh

# 4. Deploy
cd infrastructure/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f kafka-statefulset.yaml

# Wait for infrastructure
kubectl wait --for=condition=ready pod -l app=postgres -n vanguard --timeout=180s
kubectl wait --for=condition=ready pod -l app=kafka -n vanguard --timeout=300s

# Deploy services
kubectl apply -f guardrail-deployment.yaml
kubectl apply -f inventory-deployment.yaml
kubectl apply -f maintenance-deployment.yaml
kubectl apply -f agent-deployment.yaml
kubectl apply -f simulator-deployment.yaml
```

---

## Testing

### Health Checks
```bash
kubectl port-forward -n vanguard svc/inventory-service 8082:8082
curl http://localhost:8082/actuator/health
```

### View Logs
```bash
kubectl logs -f deployment/ai-agents -n vanguard
kubectl logs -f deployment/inventory-service -n vanguard
```

### Access Database
```bash
kubectl exec -it statefulset/postgres -n vanguard -- psql -U vanguard -d vanguard
```

---

## Monitoring

### Resource Usage
```bash
kubectl top pods -n vanguard
kubectl top nodes
```

### Audit Logs
```bash
kubectl port-forward -n vanguard svc/guardrail-service 8083:8083
curl http://localhost:8083/api/guardrail/audit/stats
```

---

## Scaling
```bash
# Scale inventory service
kubectl scale deployment/inventory-service -n vanguard --replicas=5

# Scale AI agents
kubectl scale deployment/ai-agents -n vanguard --replicas=3
```

---

## Cleanup
```bash
# Delete everything
kubectl delete namespace vanguard

# Stop Minikube
minikube stop
```

---

## Production Deployment

### Prerequisites
- AWS Account with EKS access
- kubectl configured for EKS cluster
- ECR repository for Docker images

### Steps
1. Build and push images to ECR
2. Update image references in deployment YAMLs
3. Configure persistent volume storage (EBS)
4. Set up ingress controller (AWS ALB)
5. Configure SSL/TLS certificates
6. Enable cluster autoscaling
7. Set up monitoring (Prometheus/Grafana)

**See detailed production deployment guide in** `docs/production-deployment.md`
