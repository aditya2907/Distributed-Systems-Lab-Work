# Lab 3 — Designing for Resilience and Observability

## Introduction
Purpose: Demonstrate patterns for resilience in distributed systems—Circuit Breaker, Retries (exponential backoff + jitter), and Chaos Engineering—on a simple ClientService -> BackendService setup deployed to Kubernetes.

Technologies:
- Python Flask services
- tenacity (retries) and pybreaker (circuit breaker)
- Docker & Kubernetes (ClusterIP services)
- Logging for observability
- Chaos experiment via `kubectl scale` (kill backend pods)


```bash
# 1. Start Minikube
minikube start

# 2. Build images in Minikube
eval $(minikube docker-env)
docker build -t backend-service:latest ./backend_service
docker build -t client-service:latest ./client_service

# 3. Deploy to Kubernetes
kubectl apply -f k8s/

# 4. Port-forward services
kubectl port-forward service/clientservice 5001:5000 &
kubectl port-forward service/backendservice 5002:5000 &

# 5. Run comprehensive tests
./enhanced_demo.sh

# 6. Run chaos experiment
cd chaos && chaos run experiment.json
```
