"""
Order Service - Microservice for managing customer orders
"""

from flask import Flask, jsonify, request
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import requests
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INVENTORY_SERVICE_URL = os.environ.get(
    'INVENTORY_SERVICE_URL', 
    'http://localhost:5001'
)
PAYMENT_SERVICE_URL = os.environ.get(
    'PAYMENT_SERVICE_URL',
    'http://localhost:5002'
)

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'microservices_db')

# Initialize MongoDB connection
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGO_DB]
    orders_collection = db['orders']
    logger.info(f"✅ Connected to MongoDB: {MONGO_URI}")
    USE_MONGODB = True
except ConnectionFailure as e:
    logger.warning(f"⚠️  MongoDB connection failed: {e}. Using in-memory storage.")
    USE_MONGODB = False

# In-memory fallback
orders_memory = {}
order_counter = 1

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "order-service",
        "inventory_service": INVENTORY_SERVICE_URL,
        "payment_service": PAYMENT_SERVICE_URL,
        "storage": "MongoDB" if USE_MONGODB else "In-Memory"
    }), 200

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """Show all orders we've received so far"""
    logger.info("Getting the full list of orders")
    
    if USE_MONGODB:
        orders_list = list(orders_collection.find({}, {'_id': 0}))
    else:
        orders_list = list(orders_memory.values())
    
    return jsonify({
        "orders": orders_list,
        "total_orders": len(orders_list),
        "timestamp": datetime.now().isoformat(),
        "storage": "MongoDB" if USE_MONGODB else "In-Memory"
    }), 200

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get details for a specific order"""
    logger.info(f"Looking up order: {order_id}")
    
    if USE_MONGODB:
        order = orders_collection.find_one({"order_id": order_id}, {'_id': 0})
    else:
        order = orders_memory.get(order_id)
    
    if not order:
        logger.warning(f"Order not found: {order_id}")
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(order), 200

@app.route('/orders', methods=['POST'])
def create_order():
    """
    Create a new order (no payment yet)
    This is like a customer saying "I want to buy X" and we check if we have it in stock.
    """
    global order_counter
    
    data = request.get_json()
    
    # Make sure we got all the info we need
    required_fields = ['customer_name', 'product_id', 'quantity']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400
    
    customer_name = data['customer_name']
    product_id = data['product_id']
    quantity = data['quantity']
    
    logger.info(f"New order: {customer_name} wants {quantity}x {product_id}")
    
    # Step 1: Get product info from Inventory Service
    try:
        product_response = requests.get(
            f"{INVENTORY_SERVICE_URL}/inventory/{product_id}",
            timeout=5
        )
        
        if product_response.status_code == 404:
            return jsonify({"error": "Product not found"}), 404
        
        product_response.raise_for_status()
        product_data = product_response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't reach inventory service: {e}")
        return jsonify({
            "error": "Inventory service unavailable",
            "details": str(e)
        }), 503
    
    # Step 2: Check if we have enough in stock
    try:
        availability_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/{product_id}/check",
            json={"quantity": quantity},
            timeout=5
        )
        availability_response.raise_for_status()
        availability_data = availability_response.json()
        
        if not availability_data.get('available', False):
            return jsonify({
                "error": "Not enough in stock",
                "requested": quantity,
                "available": availability_data.get('current_stock', 0)
            }), 400
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't check stock: {e}")
        return jsonify({
            "error": "Failed to check inventory",
            "details": str(e)
        }), 503
    
    # Step 3: Reserve the stock
    try:
        reserve_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/{product_id}/reserve",
            json={"quantity": quantity},
            timeout=5
        )
        reserve_response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't reserve stock: {e}")
        return jsonify({
            "error": "Failed to reserve inventory",
            "details": str(e)
        }), 503
    
    # Step 4: Actually create the order
    global order_counter
    
    if USE_MONGODB:
        # Get the next order number from MongoDB
        last_order = orders_collection.find_one(sort=[("order_id", -1)])
        if last_order:
            last_num = int(last_order['order_id'].replace('ORD', ''))
            order_counter = last_num + 1
    
    order_id = f"ORD{order_counter:05d}"
    order_counter += 1
    
    order = {
        "order_id": order_id,
        "customer_name": customer_name,
        "product_id": product_id,
        "product_name": product_data.get('name', 'Unknown'),
        "quantity": quantity,
        "unit_price": product_data.get('price', 0),
        "total_price": product_data.get('price', 0) * quantity,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    if USE_MONGODB:
        orders_collection.insert_one(order.copy())
    else:
        orders_memory[order_id] = order
    
    logger.info(f"Order created! ID: {order_id}")
    
    return jsonify(order), 201

@app.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """
    Cancel an order and put the stock back (compensating transaction)
    """
    logger.info(f"Cancelling order: {order_id}")
    
    if USE_MONGODB:
        order = orders_collection.find_one({"order_id": order_id}, {'_id': 0})
    else:
        order = orders_memory.get(order_id)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if order['status'] == 'cancelled':
        return jsonify({"error": "Order already cancelled"}), 400
    
    # Give the stock back to inventory
    try:
        release_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/{order['product_id']}/release",
            json={"quantity": order['quantity']},
            timeout=5
        )
        release_response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't release inventory: {e}")
        return jsonify({
            "error": "Failed to release inventory",
            "details": str(e)
        }), 503
    
    # Mark the order as cancelled
    order['status'] = 'cancelled'
    order['cancelled_at'] = datetime.now().isoformat()
    
    if USE_MONGODB:
        orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "cancelled", "cancelled_at": order['cancelled_at']}}
        )
    else:
        orders_memory[order_id] = order
    
    return jsonify(order), 200

@app.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Show some fun stats about orders"""
    if USE_MONGODB:
        orders_list = list(orders_collection.find({}, {'_id': 0}))
    else:
        orders_list = list(orders_memory.values())
    
    total_revenue = sum(order['total_price'] for order in orders_list)
    confirmed_orders = len([o for o in orders_list if o['status'] == 'confirmed'])
    cancelled_orders = len([o for o in orders_list if o['status'] == 'cancelled'])
    
    return jsonify({
        "total_orders": len(orders_list),
        "confirmed_orders": confirmed_orders,
        "cancelled_orders": cancelled_orders,
        "total_revenue": total_revenue,
        "timestamp": datetime.now().isoformat(),
        "storage": "MongoDB" if USE_MONGODB else "In-Memory"
    }), 200

@app.route('/orders/with-payment', methods=['POST'])
def create_order_with_payment():
    """
    Create a new order and process payment (full workflow)
    This is like a customer saying "I want to buy X and pay now".
    """
    global order_counter
    
    data = request.get_json()
    
    # Make sure we got all the info we need
    required_fields = ['customer_name', 'product_id', 'quantity', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400
    
    customer_name = data['customer_name']
    product_id = data['product_id']
    quantity = data['quantity']
    payment_method = data['payment_method']
    
    logger.info(f"New order with payment: {customer_name} wants {quantity}x {product_id}")
    
    # Step 1: Get product info from Inventory Service
    try:
        product_response = requests.get(
            f"{INVENTORY_SERVICE_URL}/inventory/{product_id}",
            timeout=5
        )
        
        if product_response.status_code == 404:
            return jsonify({"error": "Product not found"}), 404
        
        product_response.raise_for_status()
        product_data = product_response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't reach inventory service: {e}")
        return jsonify({
            "error": "Inventory service unavailable",
            "details": str(e)
        }), 503
    
    # Calculate total price
    total_price = product_data.get('price', 0) * quantity
    
    # Step 2: Check if payment method is valid
    try:
        payment_validate_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payments/validate",
            json={"payment_method": payment_method, "amount": total_price},
            timeout=5
        )
        
        if payment_validate_response.status_code != 200:
            return jsonify({
                "error": "Invalid payment method",
                "details": payment_validate_response.json()
            }), 400
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't validate payment: {e}")
        return jsonify({
            "error": "Payment service unavailable",
            "details": str(e)
        }), 503
    
    # Step 3: Reserve the stock
    try:
        reserve_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/{product_id}/reserve",
            json={"quantity": quantity},
            timeout=5
        )
        
        if reserve_response.status_code != 200:
            return jsonify({
                "error": "Failed to reserve inventory",
                "details": reserve_response.json()
            }), reserve_response.status_code
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't reserve stock: {e}")
        return jsonify({
            "error": "Failed to reserve inventory",
            "details": str(e)
        }), 503
    
    # Step 4: Create the order (pending payment)
    order_id = f"ORD{order_counter:05d}"
    order_counter += 1
    
    order = {
        "order_id": order_id,
        "customer_name": customer_name,
        "product_id": product_id,
        "product_name": product_data.get('name', 'Unknown'),
        "quantity": quantity,
        "unit_price": product_data.get('price', 0),
        "total_price": total_price,
        "status": "pending_payment",
        "payment_method": payment_method,
        "created_at": datetime.now().isoformat()
    }
    
    # Step 5: Try to process the payment
    try:
        payment_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payments/process",
            json={
                "order_id": order_id,
                "customer_name": customer_name,
                "amount": total_price,
                "payment_method": payment_method
            },
            timeout=5
        )
        
        payment_data = payment_response.json()
        
        if payment_response.status_code == 201 and payment_data.get('success'):
            # Payment worked! Confirm the order
            order['status'] = 'confirmed'
            order['payment_id'] = payment_data.get('payment_id')
            order['transaction_id'] = payment_data.get('transaction_id')
            order['paid_at'] = payment_data.get('processed_at')
            
            if USE_MONGODB:
                orders_collection.insert_one(order.copy())
            else:
                orders_memory[order_id] = order
            
            logger.info(f"Order with payment created! ID: {order_id}")
            
            return jsonify(order), 201
        else:
            # Payment failed - put the stock back
            logger.error(f"Payment failed for order {order_id}")
            
            try:
                requests.post(
                    f"{INVENTORY_SERVICE_URL}/inventory/{product_id}/release",
                    json={"quantity": quantity},
                    timeout=5
                )
            except Exception as release_error:
                logger.error(f"Couldn't release inventory after payment failure: {release_error}")
            
            return jsonify({
                "error": "Payment failed",
                "order_id": order_id,
                "payment_details": payment_data
            }), 402  # Payment Required
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Couldn't process payment: {e}")
        
        # Put the stock back if payment service is down
        try:
            requests.post(
                f"{INVENTORY_SERVICE_URL}/inventory/{product_id}/release",
                json={"quantity": quantity},
                timeout=5
            )
        except Exception as release_error:
            logger.error(f"Couldn't release inventory: {release_error}")
        
        return jsonify({
            "error": "Payment service unavailable",
            "details": str(e)
        }), 503

if __name__ == '__main__':
    logger.info(f"Starting Order Service on port 5000")
    logger.info(f"Inventory Service URL: {INVENTORY_SERVICE_URL}")
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
