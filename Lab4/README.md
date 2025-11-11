# Lab 4: Microservices Order Management System

## Overview
This project is a complete microservices-based order management system that demonstrates real-world architectural patterns. Think of it as a mini e-commerce backend where different teams could own different pieces:

- **API Gateway** - Your front door. All external requests come through here for security, logging, and routing
- **Order Service** - The coordinator. It talks to both inventory and payment services to complete orders
- **Inventory Service** - The warehouse manager. Keeps track of what's in stock
- **Payment Service** - The cashier. Handles all payment processing independently

Right now, we're running **4 services with 8 total pods** in Kubernetes (2 replicas of each service for reliability).

## Why Split Into 4 Services?

You might be wondering - why not just build one big application? Here's the thinking behind each service:

### 1. API Gateway
Think of this as the bouncer at a club. Every request goes through here first. It checks IDs (rate limiting), keeps a guest list (logging), and directs people to the right room (routing). This means we can add security, monitoring, and traffic control in one place rather than in every service.

### 2. Order Service
This is the coordinator - it doesn't do everything itself, but it knows who to talk to. When an order comes in, it checks with the inventory service (do we have it?), talks to the payment service (can they pay?), and then confirms the order. If something goes wrong, it knows how to clean up (compensating transactions).

### 3. Inventory Service
The warehouse manager. It knows what products we have and how many. During Black Friday sales, this service might need way more replicas than the others. By keeping it separate, we can scale it independently without touching order or payment processing.

### 4. Payment Service
The most security-sensitive part. Payment processing has strict compliance requirements (PCI DSS). By isolating it, we create a clear security boundary. If there's a security audit, they only need to look at this one service. Plus, if it goes down, people can still browse inventory.

### How Services Talk to Each Other

**From the Outside (Users → API Gateway)**
Everything comes through port 30080. The gateway decides where each request should go based on the URL path. This gives us one place to add authentication, rate limiting (we allow 100 requests per minute per IP), and logging.

**Between Services (Internal)**
Services talk to each other using REST APIs over HTTP. Kubernetes handles service discovery automatically - so the order service just calls `http://inventory-service:5001` and Kubernetes figures out which pod to route to.

**Why We Chose This Approach:**
- It's straightforward to implement and debug (you can just curl endpoints)
- Perfect for operations that need immediate answers (checking stock, processing payments)
- Keeps data consistent during transactions

**The Downsides:**
- Services depend on each other being available
- If one service is slow, it can slow down the whole chain
- We need to handle failures carefully (more on compensating transactions below)

**Patterns We're Using:**
- **Orchestration**: Order service is the "brain" that coordinates everything
- **Compensating Transactions**: If payment fails, we release the reserved inventory
- **Timeouts**: Every service call has a 10-second timeout to prevent hanging forever
- **Health Checks**: Kubernetes automatically restarts unhealthy pods

### Technology Stack
- **Language**: Python 3.11
- **Framework**: Flask 3.0.0 (lightweight, production-ready)
- **HTTP Client**: Requests 2.31.0 (for inter-service communication)
- **Containerization**: Docker with python:3.11-slim (~240MB per image)
- **Orchestration**: Kubernetes (Docker Desktop / Minikube)
- **API Communication**: REST with JSON
- **Service Discovery**: Kubernetes DNS
- **Load Balancing**: Kubernetes native (round-robin)
- **Networking**: ClusterIP (internal) + NodePort (external)


## The Trade-offs We Made

### Why Not Just One Big Service?

**The Benefits of Splitting:**
1. **Different teams can work independently** - The payment team doesn't need to coordinate with the inventory team for deployments
2. **Scale what needs scaling** - During a sale, inventory gets hammered with requests. We can scale just that service without touching the others
3. **Failures stay isolated** - If payment processing breaks, people can still browse products
4. **Security boundaries are clearer** - PCI compliance requirements only apply to the payment service
5. **Different update schedules** - We can update payment integrations without touching order logic

**The Costs of Splitting:**
1. **More complexity** - We went from 1 thing to manage to 4 things
2. **Network calls add latency** - Instead of function calls (nanoseconds), we have HTTP calls (milliseconds)
3. **Distributed transactions are hard** - When payment fails, we need to explicitly release the inventory we reserved
4. **More moving parts** - More services mean more things that can go wrong

**What We Decided:**
We went with 4 services because this project is about learning microservices patterns. In the real world, you'd start with one service and only split when you have a good reason (like the ones above). The key is knowing the trade-offs and making conscious decisions.

### Communication Pattern
**Decision**: API Gateway + Synchronous REST

**API Gateway Benefits**:
- ✅ Single entry point for external clients
- ✅ Centralized authentication/authorization point
- ✅ Request logging and monitoring
- ✅ Rate limiting and DDoS protection
- ✅ Service discovery abstraction
- ✅ Version management capability

**Synchronous REST Pros**:
- ✅ Simple implementation
- ✅ Immediate consistency for critical operations
- ✅ Easy debugging with clear request/response flow
- ✅ Suitable for real-time inventory checks
- ✅ Strong consistency within transaction scope

**Synchronous REST Cons**:
- ❌ Tight coupling between services
- ❌ Cascading failures possible (mitigated with timeouts)
- ❌ Synchronous blocking (mitigated with async patterns)
- ❌ Service availability dependencies

**Resilience Patterns Implemented**:
1. **Timeouts**: 10-second timeout on all service calls
2. **Compensating Transactions**: Inventory released on payment failure
3. **Health Checks**: Liveness and readiness probes
4. **Circuit Breaker Concepts**: Timeout → 504 error
5. **Error Handling**: Graceful degradation with meaningful errors

**Alternative for Future**: 
- Message queue (RabbitMQ/Kafka) for async operations
- Event-driven architecture with eventual consistency
- CQRS pattern for read-heavy operations

### Service Mesh Concepts
**Implementation**: Practical patterns without full service mesh (Istio/Linkerd)

**What We Implemented**:
1. **Service Discovery**: Kubernetes DNS + API Gateway registry
2. **Traffic Management**: Centralized routing, load balancing
3. **Observability**: Logging, metrics, health monitoring
4. **Resilience**: Timeouts, error handling, health probes
5. **Security**: Rate limiting, internal-only services (ClusterIP)

**Benefits Demonstrated**:
- Centralized management and policies
- Request tracking across services
- Performance metrics collection
- Fault tolerance patterns
- Security best practices

**When to Use Full Service Mesh** (Istio/Linkerd):
- Complex microservices (10+ services)
- Need for advanced traffic routing (canary, A/B testing)
- mTLS between all services required
- Distributed tracing with Jaeger/Zipkin
- Advanced circuit breaking and retries
- Multi-cluster deployments

## Key Features Implemented

### 1. API Gateway ✅
- Unified entry point (Port 30080)
- Request routing to appropriate services
- Centralized logging with timestamps
- Rate limiting (100 req/min per IP)
- Health monitoring of backend services
- Metrics collection (requests, success rate, response times)
- Error handling (timeouts, connection errors)

### 2. Service Mesh Concepts ✅
- **Service Discovery**: Kubernetes DNS + configuration
- **Traffic Management**: Centralized routing, load balancing
- **Observability**: Logging, metrics, health checks
- **Resilience**: Timeouts, circuit breaker concepts, health probes
- **Security**: Rate limiting, internal-only services

### 3. Distributed Transactions ✅
- Order orchestration across services
- Compensating transactions (rollback on failure)
- 5-step workflow: Validate → Reserve → Pay → Confirm → Return
- Inventory release on payment failure

### 4. Microservices Best Practices ✅
- Service isolation (4 independent services)
- Health checks (liveness + readiness probes)
- Resource limits (CPU, memory)
- Horizontal scaling (2 replicas per service)
- Container optimization (slim images, ~240MB)
- Environment-based configuration
- Graceful error handling

### 5. Kubernetes Patterns ✅
- Deployments with replica sets
- Services (NodePort + ClusterIP)
- Service discovery via DNS
- Load balancing (round-robin)
- Rolling updates support
- Self-healing (auto-restart on failure)

## Monitoring & Observability

### View Logs
```bash
# API Gateway logs (centralized)
kubectl logs -l app=api-gateway --tail=100 -f

# Order Service logs
kubectl logs -l app=order-service --tail=50

# All service logs
kubectl logs -l tier=backend --tail=20 --all-containers=true
```

### Check Metrics
```bash
# API Gateway metrics
curl http://localhost:30080/metrics

# Service mesh traffic statistics
curl http://localhost:30080/mesh/traffic-stats

# Service health status
curl http://localhost:30080/mesh/service-status
```


- Use port-forwarding: `kubectl port-forward service/api-gateway 30080:8080`


## Cleanup

### Delete Kubernetes Resources
```bash
kubectl delete -f k8s/

# Or delete individually
kubectl delete deployment api-gateway order-service inventory-service payment-service
kubectl delete service api-gateway order-service inventory-service payment-service
```

### Remove Docker Images
```bash
docker rmi api-gateway:latest
docker rmi order-service:latest
docker rmi inventory-service:latest
docker rmi payment-service:latest

# Or remove all at once
docker rmi $(docker images | grep -E "api-gateway|order-service|inventory-service|payment-service" | awk '{print $3}')
```

### Clean Build Artifacts
```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -f
```
