"""
API Gateway - Unified entry point for microservices
"""

from flask import Flask, jsonify, request, g
import requests
import logging
import os
import time
from datetime import datetime
from functools import wraps

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs (Service Discovery)
SERVICES = {
    'order': os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5000'),
    'inventory': os.environ.get('INVENTORY_SERVICE_URL', 'http://localhost:5001'),
    'payment': os.environ.get('PAYMENT_SERVICE_URL', 'http://localhost:5002')
}

# Simple in-memory rate limiting
request_counts = {}
RATE_LIMIT = 100  # requests per minute per IP

# Request tracking for observability
request_metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'average_response_time': 0,
    'requests_by_service': {
        'order': 0,
        'inventory': 0,
        'payment': 0
    }
}


def log_request():
    """Middleware for logging all incoming requests"""
    g.start_time = time.time()
    client_ip = request.remote_addr
    logger.info(f"Incoming request: {request.method} {request.path} from {client_ip}")


def log_response(response):
    """Log response details and metrics"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Duration: {duration:.3f}s - "
            f"Path: {request.path}"
        )
        
        # Update metrics
        request_metrics['total_requests'] += 1
        if response.status_code < 400:
            request_metrics['successful_requests'] += 1
        else:
            request_metrics['failed_requests'] += 1
        
        # Update average response time
        total = request_metrics['total_requests']
        current_avg = request_metrics['average_response_time']
        request_metrics['average_response_time'] = (
            (current_avg * (total - 1) + duration) / total
        )
    
    return response


# Register middleware
app.before_request(log_request)
app.after_request(log_response)


def rate_limit_check():
    """Simple rate limiting by IP address"""
    client_ip = request.remote_addr
    current_minute = int(time.time() / 60)
    key = f"{client_ip}:{current_minute}"
    
    if key not in request_counts:
        request_counts[key] = 0
    
    request_counts[key] += 1
    
    if request_counts[key] > RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return False
    
    return True


def require_rate_limit(f):
    """Decorator to enforce rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limit_check():
            return jsonify({
                "error": "Rate limit exceeded",
                "limit": RATE_LIMIT,
                "message": "Too many requests. Please try again later."
            }), 429
        return f(*args, **kwargs)
    return decorated_function


def route_to_service(service_name, path, method='GET', data=None, params=None):
    """
    Route request to appropriate microservice
    Implements service mesh routing concept
    """
    service_url = SERVICES.get(service_name)
    
    if not service_url:
        logger.error(f"Unknown service: {service_name}")
        return jsonify({"error": f"Service {service_name} not found"}), 404
    
    full_url = f"{service_url}{path}"
    logger.info(f"Routing to {service_name}: {method} {full_url}")
    
    # Track service usage
    request_metrics['requests_by_service'][service_name] += 1
    
    try:
        # Forward request to microservice
        if method == 'GET':
            response = requests.get(full_url, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(
                full_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        elif method == 'PUT':
            response = requests.put(
                full_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        elif method == 'DELETE':
            response = requests.delete(full_url, timeout=10)
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # Log service response
        logger.info(
            f"Service {service_name} responded: "
            f"{response.status_code} in {response.elapsed.total_seconds():.3f}s"
        )
        
        return response.json(), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout calling {service_name}")
        return jsonify({
            "error": "Service timeout",
            "service": service_name,
            "message": "The service took too long to respond"
        }), 504
    
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {service_name}")
        return jsonify({
            "error": "Service unavailable",
            "service": service_name,
            "message": "Could not connect to the service"
        }), 503
    
    except Exception as e:
        logger.error(f"Error routing to {service_name}: {str(e)}")
        return jsonify({
            "error": "Gateway error",
            "message": str(e)
        }), 500


# ============================================================================
# API GATEWAY ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """API Gateway health check"""
    return jsonify({
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat(),
        "services": SERVICES
    }), 200


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get API Gateway metrics (Service Mesh concept)"""
    return jsonify({
        "metrics": request_metrics,
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# ORDER SERVICE ROUTES
# ============================================================================

@app.route('/api/orders', methods=['GET'])
@require_rate_limit
def get_orders():
    """Get all orders"""
    return route_to_service('order', '/orders', method='GET')


@app.route('/api/orders/<order_id>', methods=['GET'])
@require_rate_limit
def get_order(order_id):
    """Get specific order"""
    return route_to_service('order', f'/orders/{order_id}', method='GET')


@app.route('/api/orders', methods=['POST'])
@require_rate_limit
def create_order():
    """Create new order"""
    return route_to_service('order', '/orders', method='POST', data=request.json)


@app.route('/api/orders/with-payment', methods=['POST'])
@require_rate_limit
def create_order_with_payment():
    """Create order with payment"""
    return route_to_service(
        'order',
        '/orders/with-payment',
        method='POST',
        data=request.json
    )


@app.route('/api/orders/<order_id>/cancel', methods=['POST'])
@require_rate_limit
def cancel_order(order_id):
    """Cancel an order"""
    return route_to_service('order', f'/orders/{order_id}/cancel', method='POST')


@app.route('/api/orders/stats', methods=['GET'])
@require_rate_limit
def get_order_stats():
    """Get order statistics"""
    return route_to_service('order', '/orders/stats', method='GET')


# ============================================================================
# INVENTORY SERVICE ROUTES
# ============================================================================

@app.route('/api/inventory', methods=['GET'])
@require_rate_limit
def get_inventory():
    """Get all inventory"""
    return route_to_service('inventory', '/inventory', method='GET')


@app.route('/api/inventory/<product_id>', methods=['GET'])
@require_rate_limit
def get_product(product_id):
    """Get specific product"""
    return route_to_service('inventory', f'/inventory/{product_id}', method='GET')


@app.route('/api/inventory/<product_id>', methods=['PUT'])
@require_rate_limit
def update_product(product_id):
    """Update product inventory"""
    return route_to_service(
        'inventory',
        f'/inventory/{product_id}',
        method='PUT',
        data=request.json
    )


# ============================================================================
# PAYMENT SERVICE ROUTES
# ============================================================================

@app.route('/api/payments', methods=['GET'])
@require_rate_limit
def get_payments():
    """Get all payments"""
    return route_to_service('payment', '/payments', method='GET')


@app.route('/api/payments/<payment_id>', methods=['GET'])
@require_rate_limit
def get_payment(payment_id):
    """Get specific payment"""
    return route_to_service('payment', f'/payments/{payment_id}', method='GET')


@app.route('/api/payments/stats', methods=['GET'])
@require_rate_limit
def get_payment_stats():
    """Get payment statistics"""
    return route_to_service('payment', '/payments/stats', method='GET')


# ============================================================================
# SERVICE MESH - TRAFFIC MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/mesh/service-status', methods=['GET'])
def get_service_status():
    """
    Check health of all backend services
    Service Mesh concept: Health monitoring
    """
    status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            status[service_name] = {
                "status": "unavailable",
                "error": str(e)
            }
    
    return jsonify({
        "services": status,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/mesh/traffic-stats', methods=['GET'])
def get_traffic_stats():
    """
    Get traffic statistics across services
    Service Mesh concept: Traffic monitoring
    """
    return jsonify({
        "total_requests": request_metrics['total_requests'],
        "successful_requests": request_metrics['successful_requests'],
        "failed_requests": request_metrics['failed_requests'],
        "success_rate": (
            request_metrics['successful_requests'] / request_metrics['total_requests'] * 100
            if request_metrics['total_requests'] > 0 else 0
        ),
        "average_response_time": request_metrics['average_response_time'],
        "requests_by_service": request_metrics['requests_by_service'],
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/mesh/route-info', methods=['GET'])
def get_route_info():
    """
    Get routing information
    Service Mesh concept: Service discovery
    """
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                "path": str(rule),
                "methods": list(rule.methods - {'HEAD', 'OPTIONS'}),
                "endpoint": rule.endpoint
            })
    
    return jsonify({
        "routes": routes,
        "total_routes": len(routes),
        "services": SERVICES
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        "error": "Not Found",
        "message": f"The requested URL {request.path} was not found",
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500


if __name__ == '__main__':
    logger.info("Starting API Gateway on port 8080")
    logger.info(f"Configured services: {SERVICES}")
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=8080, debug=debug_mode)
