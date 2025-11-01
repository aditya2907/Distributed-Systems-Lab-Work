#!/bin/bash
# Scale backend to 1 replica for clearer demonstration
echo "Scaling backend service to 1 replica for clearer failure demonstration..."
kubectl scale deployment backendservice-deployment --replicas=1
sleep 5

echo "Current backend pods:"
kubectl get pods -l app=backend
echo ""

# Test 1: Demonstrate Retry Pattern with Detailed Logging
echo "========================================="
echo "TEST 1: Retry Pattern with Exponential Backoff"
echo "========================================="
echo ""
echo "Configuring backend: 80% failure rate with 503 errors..."
curl -s -X POST http://localhost:5002/config/failure \
    -H "Content-Type: application/json" \
    -d '{"failure_rate": 0.8, "status_code": 503}' | jq '.'

echo ""
echo "Sending a request (watch for retry attempts in logs)..."
POD_NAME=$(kubectl get pods -l app=client -o jsonpath='{.items[0].metadata.name}')

# Send request
curl -s http://localhost:5001/fetch | jq '.'

echo ""
echo "Client Pod Logs (Last 15 lines - showing retry behavior):"
kubectl logs $POD_NAME --tail=15
echo ""

Test 2: Circuit Breaker Opening
echo "========================================="
echo "TEST 2: Circuit Breaker Opening"
echo "========================================="
echo ""
echo "Configuring backend: 80% failure rate with 500 errors..."
curl -s -X POST http://localhost:5002/config/failure \
    -H "Content-Type: application/json" \
    -d '{"failure_rate": 0.8, "status_code": 500}' | jq '.'

echo ""
echo "Sending 5 requests to trigger circuit breaker opening..."
for i in {1..5}; do
    echo "  Request $i:"
    curl -s http://localhost:5001/fetch | jq -c '{status, message}'
    sleep 1
done

echo ""
echo "Circuit Breaker should now be OPEN. Next request will fail immediately:"
curl -s http://localhost:5001/fetch | jq -c '{status, message}'

echo ""
echo "Client Pod Logs (showing circuit breaker state):"
kubectl logs $POD_NAME --tail=25 | grep -E "(Circuit|circuit|OPEN|failure count)"
echo ""

# Test 3: Pod Failure During Active Load
echo "========================================="
echo "TEST 3: Pod Failure Simulation"
echo "========================================="
echo ""

# Reset backend first
echo "Resetting backend to healthy state..."
curl -s -X POST http://localhost:5002/config/failure \
    -H "Content-Type: application/json" \
    -d '{"failure_rate": 0.0}' > /dev/null
sleep 2

# Wait for circuit to close
echo "Waiting 15s for circuit breaker to reset..."
sleep 15

# Verify system is healthy
echo "Verifying system health:"
curl -s http://localhost:5001/fetch | jq -c '{status}'

echo ""
echo "Starting continuous load in background..."
# Create a background load script
cat > /tmp/load_test.sh << 'EOF'
#!/bin/bash
for i in {1..20}; do
    RESPONSE=$(curl -s -m 3 http://localhost:5001/fetch 2>&1)
    if echo "$RESPONSE" | grep -q '"status"'; then
        STATUS=$(echo "$RESPONSE" | jq -r '.status')
        echo "[$(date +%H:%M:%S)] Request $i: $STATUS"
    else
        echo "[$(date +%H:%M:%S)] Request $i: FAILED/TIMEOUT"
    fi
    sleep 2
done
EOF

chmod +x /tmp/load_test.sh
/tmp/load_test.sh &
LOAD_PID=$!

sleep 5

echo "KILLING BACKEND POD NOW..."
BACKEND_POD=$(kubectl get pods -l app=backend -o jsonpath='{.items[0].metadata.name}')
echo "Terminating pod: $BACKEND_POD"
kubectl delete pod $BACKEND_POD --force --grace-period=0 > /dev/null 2>&1

# Wait for load test to complete
wait $LOAD_PID

echo ""
echo "Pod status after chaos:"
kubectl get pods -l app=backend

echo ""
echo "Client logs during pod failure:"
kubectl logs $POD_NAME --tail=40 | tail -20

# echo ""
# echo "========================================="
# echo "SUMMARY OF OBSERVATIONS"
# echo "========================================="
# echo "1. Retry Pattern: Retries with exponential backoff successfully"
# echo "   handled transient failures"
# echo ""
# echo "2. Circuit Breaker: Opened after 3 failures, protecting the"
# echo "   client from cascading failures"
# echo ""
# echo "3. Chaos Resilience: System continued operating during pod"
# echo "   failure, with Kubernetes auto-recovery"
# echo ""
# echo "For detailed analysis, check:"
# echo "  - kubectl logs $POD_NAME"
# echo "  - kubectl get events"
# echo "========================================="
