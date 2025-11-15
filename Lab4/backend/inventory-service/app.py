"""
Inventory Service - Microservice for managing product inventory
"""

from flask import Flask, jsonify, request
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'microservices_db')

# Initialize MongoDB connection
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    mongo_client.admin.command('ping')
    db = mongo_client[MONGO_DB]
    inventory_collection = db['inventory']
    logger.info(f"✅ Connected to MongoDB: {MONGO_URI}")
    USE_MONGODB = True
except ConnectionFailure as e:
    logger.warning(f"⚠️  MongoDB connection failed: {e}. Using in-memory storage.")
    USE_MONGODB = False

# In-memory inventory database (fallback when MongoDB is unavailable)
inventory_memory = {
    "PROD001": {"name": "Laptop", "stock": 10, "price": 999.99},
    "PROD002": {"name": "Mouse", "stock": 50, "price": 29.99},
    "PROD003": {"name": "Keyboard", "stock": 30, "price": 79.99},
    "PROD004": {"name": "Monitor", "stock": 15, "price": 299.99},
    "PROD005": {"name": "Headphones", "stock": 25, "price": 149.99}
}

def initialize_inventory():
    """Initialize MongoDB with default inventory if empty"""
    if USE_MONGODB:
        if inventory_collection.count_documents({}) == 0:
            logger.info("Initializing MongoDB with default inventory...")
            for product_id, product_data in inventory_memory.items():
                inventory_collection.insert_one({
                    "product_id": product_id,
                    **product_data
                })
            logger.info("✅ Inventory initialized in MongoDB")

# Initialize inventory on startup
initialize_inventory()

def get_inventory():
    """Get all inventory items from MongoDB or memory"""
    if USE_MONGODB:
        items = list(inventory_collection.find({}, {'_id': 0}))
        return {item['product_id']: {k: v for k, v in item.items() if k != 'product_id'} for item in items}
    return inventory_memory.copy()

def get_product_from_db(product_id):
    """Get a single product from MongoDB or memory"""
    if USE_MONGODB:
        product = inventory_collection.find_one({"product_id": product_id}, {'_id': 0})
        if product:
            return {k: v for k, v in product.items() if k != 'product_id'}
    return inventory_memory.get(product_id)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes"""
    return jsonify({"status": "healthy", "service": "inventory-service"}), 200

@app.route('/inventory', methods=['GET'])
def get_all_inventory():
    """Get all products in inventory"""
    logger.info("Fetching all inventory items")
    inventory = get_inventory()
    return jsonify({
        "inventory": inventory,
        "total_products": len(inventory),
        "timestamp": datetime.now().isoformat(),
        "storage": "MongoDB" if USE_MONGODB else "In-Memory"
    }), 200

@app.route('/inventory/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product details"""
    logger.info(f"Fetching product: {product_id}")
    
    product = get_product_from_db(product_id)
    if not product:
        logger.warning(f"Product not found: {product_id}")
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({
        "product_id": product_id,
        **product
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
    
    product = get_product_from_db(product_id)
    if not product:
        return jsonify({
            "available": False,
            "error": "Product not found"
        }), 404
    
    current_stock = product["stock"]
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
    
    product = get_product_from_db(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product["stock"] < quantity:
        logger.warning(f"Insufficient stock for {product_id}")
        return jsonify({
            "success": False,
            "error": "Insufficient stock",
            "available": product["stock"]
        }), 400
    
    # Reserve the stock in MongoDB or memory
    new_stock = product["stock"] - quantity
    if USE_MONGODB:
        inventory_collection.update_one(
            {"product_id": product_id},
            {"$set": {"stock": new_stock}}
        )
    else:
        inventory_memory[product_id]["stock"] = new_stock
    
    logger.info(f"Reserved {quantity} units of {product_id}. Remaining: {new_stock}")
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        "reserved_quantity": quantity,
        "remaining_stock": new_stock
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
    
    product = get_product_from_db(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Release the stock in MongoDB or memory
    new_stock = product["stock"] + quantity
    if USE_MONGODB:
        inventory_collection.update_one(
            {"product_id": product_id},
            {"$set": {"stock": new_stock}}
        )
    else:
        inventory_memory[product_id]["stock"] = new_stock
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        "released_quantity": quantity,
        "current_stock": new_stock
    }), 200

@app.route('/inventory/<product_id>', methods=['PUT'])
def update_inventory(product_id):
    """Update inventory stock levels (admin operation)"""
    data = request.get_json()
    
    product = get_product_from_db(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    update_data = {}
    if 'stock' in data:
        update_data['stock'] = data['stock']
    if 'price' in data:
        update_data['price'] = data['price']
    
    if USE_MONGODB:
        inventory_collection.update_one(
            {"product_id": product_id},
            {"$set": update_data}
        )
        updated_product = inventory_collection.find_one({"product_id": product_id}, {'_id': 0})
        result = {k: v for k, v in updated_product.items() if k != 'product_id'}
    else:
        inventory_memory[product_id].update(update_data)
        result = inventory_memory[product_id]
    
    logger.info(f"Updated inventory for {product_id}")
    
    return jsonify({
        "success": True,
        "product_id": product_id,
        **result
    }), 200

if __name__ == '__main__':
    logger.info("Starting Inventory Service on port 5001")
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
