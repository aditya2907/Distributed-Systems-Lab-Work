"""
Inventory Service - Microservice for managing product inventory
"""

from flask import Flask, jsonify, request
from datetime import datetime
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory inventory database (simulating persistent storage)
inventory = {
    "PROD001": {"name": "Laptop", "stock": 10, "price": 999.99},
    "PROD002": {"name": "Mouse", "stock": 50, "price": 29.99},
    "PROD003": {"name": "Keyboard", "stock": 30, "price": 79.99},
    "PROD004": {"name": "Monitor", "stock": 15, "price": 299.99},
    "PROD005": {"name": "Headphones", "stock": 25, "price": 149.99}
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes"""
    return jsonify({"status": "healthy", "service": "inventory-service"}), 200

@app.route('/inventory', methods=['GET'])
def get_all_inventory():
    """Get all products in inventory"""
    logger.info("Fetching all inventory items")
    return jsonify({
        "inventory": inventory,
        "total_products": len(inventory),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/inventory/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product details"""
    logger.info(f"Fetching product: {product_id}")
    
    if product_id not in inventory:
        logger.warning(f"Product not found: {product_id}")
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({
        "product_id": product_id,
        **inventory[product_id]
    }), 200

@app.route('/inventory/<product_id>/check', methods=['POST'])
def check_availability(product_id):
    """
    Check if product has sufficient stock
    Used by Order Service before creating orders
    """
    data = request.get_json()
    requested_quantity = data.get('quantity', 0)
    
    logger.info(f"Checking availability for {product_id}, quantity: {requested_quantity}")
    
    if product_id not in inventory:
        return jsonify({
            "available": False,
            "error": "Product not found"
        }), 404
    
    current_stock = inventory[product_id]["stock"]
    available = current_stock >= requested_quantity
    
    return jsonify({
        "product_id": product_id,
        "requested_quantity": requested_quantity,
        "current_stock": current_stock,
        "available": available
    }), 200

@app.route('/inventory/<product_id>/reserve', methods=['POST'])
def reserve_stock(product_id):
    """
    Reserve stock for an order
    Demonstrates inter-service communication pattern
    """
    data = request.get_json()
    quantity = data.get('quantity', 0)
    
    logger.info(f"Attempting to reserve {quantity} units of {product_id}")
    
    if product_id not in inventory:
        return jsonify({"error": "Product not found"}), 404
    
    if inventory[product_id]["stock"] < quantity:
        logger.warning(f"Insufficient stock for {product_id}")
        return jsonify({
            "success": False,
            "error": "Insufficient stock",
            "available": inventory[product_id]["stock"]
        }), 400
    
    # Reserve the stock
    inventory[product_id]["stock"] -= quantity
    logger.info(f"Reserved {quantity} units of {product_id}. Remaining: {inventory[product_id]['stock']}")
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        "reserved_quantity": quantity,
        "remaining_stock": inventory[product_id]["stock"]
    }), 200

@app.route('/inventory/<product_id>/release', methods=['POST'])
def release_stock(product_id):
    """
    Release reserved stock (e.g., if order is cancelled)
    Demonstrates compensating transaction pattern
    """
    data = request.get_json()
    quantity = data.get('quantity', 0)
    
    logger.info(f"Releasing {quantity} units of {product_id}")
    
    if product_id not in inventory:
        return jsonify({"error": "Product not found"}), 404
    
    inventory[product_id]["stock"] += quantity
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        "released_quantity": quantity,
        "current_stock": inventory[product_id]["stock"]
    }), 200

@app.route('/inventory/<product_id>', methods=['PUT'])
def update_inventory(product_id):
    """Update inventory stock levels (admin operation)"""
    data = request.get_json()
    
    if product_id not in inventory:
        return jsonify({"error": "Product not found"}), 404
    
    if 'stock' in data:
        inventory[product_id]["stock"] = data['stock']
    if 'price' in data:
        inventory[product_id]["price"] = data['price']
    
    logger.info(f"Updated inventory for {product_id}")
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        **inventory[product_id]
    }), 200

if __name__ == '__main__':
    logger.info("Starting Inventory Service on port 5001")
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
