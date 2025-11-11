"""
Payment Service - Microservice for managing payment processing
"""

from flask import Flask, jsonify, request
from datetime import datetime
import logging
import os
import random

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory payment database (simulating persistent storage)
payments = {}
payment_counter = 1

# Supported payment methods
PAYMENT_METHODS = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes"""
    return jsonify({"status": "healthy", "service": "payment-service"}), 200

@app.route('/payments', methods=['GET'])
def get_all_payments():
    """Get all payment records"""
    logger.info("Fetching all payments")
    return jsonify({
        "payments": list(payments.values()),
        "total_payments": len(payments),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Get specific payment details"""
    logger.info(f"Fetching payment: {payment_id}")
    
    if payment_id not in payments:
        logger.warning(f"Payment not found: {payment_id}")
        return jsonify({"error": "Payment not found"}), 404
    
    return jsonify(payments[payment_id]), 200

@app.route('/payments/order/<order_id>', methods=['GET'])
def get_payments_by_order(order_id):
    """Get all payments for a specific order"""
    logger.info(f"Fetching payments for order: {order_id}")
    
    order_payments = [p for p in payments.values() if p['order_id'] == order_id]
    
    return jsonify({
        "order_id": order_id,
        "payments": order_payments,
        "total_amount": sum(p['amount'] for p in order_payments if p['status'] == 'completed')
    }), 200

@app.route('/payments/validate', methods=['POST'])
def validate_payment_method():
    """
    Validate payment method and details
    Used by Order Service before processing payment
    """
    data = request.get_json()
    payment_method = data.get('payment_method', '')
    amount = data.get('amount', 0)
    
    logger.info(f"Validating payment method: {payment_method}, amount: {amount}")
    
    if payment_method not in PAYMENT_METHODS:
        return jsonify({
            "valid": False,
            "error": "Invalid payment method",
            "supported_methods": PAYMENT_METHODS
        }), 400
    
    if amount <= 0:
        return jsonify({
            "valid": False,
            "error": "Amount must be greater than 0"
        }), 400
    
    return jsonify({
        "valid": True,
        "payment_method": payment_method,
        "amount": amount
    }), 200

@app.route('/payments/process', methods=['POST'])
def process_payment():
    """
    Process a payment for an order
    Demonstrates inter-service communication pattern
    """
    global payment_counter
    
    data = request.get_json()
    
    # Validate request
    required_fields = ['order_id', 'amount', 'payment_method', 'customer_name']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": "Missing required fields",
            "required": required_fields
        }), 400
    
    order_id = data['order_id']
    amount = data['amount']
    payment_method = data['payment_method']
    customer_name = data['customer_name']
    
    logger.info(f"Processing payment for order {order_id}: ${amount} via {payment_method}")
    
    # Validate payment method
    if payment_method not in PAYMENT_METHODS:
        return jsonify({
            "success": False,
            "error": "Invalid payment method",
            "supported_methods": PAYMENT_METHODS
        }), 400
    
    # Validate amount
    if amount <= 0:
        return jsonify({
            "success": False,
            "error": "Amount must be greater than 0"
        }), 400
    
    # Simulate payment processing (90% success rate)
    # In real system, this would integrate with payment gateway
    processing_successful = random.random() < 0.9
    
    payment_id = f"PAY{payment_counter:05d}"
    payment_counter += 1
    
    if processing_successful:
        # Create payment record
        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed",
            "transaction_id": f"TXN{random.randint(100000, 999999)}",
            "processed_at": datetime.now().isoformat()
        }
        
        payments[payment_id] = payment
        logger.info(f"Payment processed successfully: {payment_id}")
        
        return jsonify({
            "success": True,
            **payment
        }), 201
    else:
        # Payment failed
        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "amount": amount,
            "payment_method": payment_method,
            "status": "failed",
            "error_code": "INSUFFICIENT_FUNDS",
            "error_message": "Payment declined by processor",
            "attempted_at": datetime.now().isoformat()
        }
        
        payments[payment_id] = payment
        logger.warning(f"Payment failed: {payment_id}")
        
        return jsonify({
            "success": False,
            **payment
        }), 400

@app.route('/payments/<payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """
    Refund a payment
    Demonstrates compensating transaction pattern
    """
    logger.info(f"Processing refund for payment: {payment_id}")
    
    if payment_id not in payments:
        return jsonify({"error": "Payment not found"}), 404
    
    payment = payments[payment_id]
    
    if payment['status'] == 'refunded':
        return jsonify({"error": "Payment already refunded"}), 400
    
    if payment['status'] != 'completed':
        return jsonify({"error": "Can only refund completed payments"}), 400
    
    # Process refund
    payment['status'] = 'refunded'
    payment['refunded_at'] = datetime.now().isoformat()
    payment['refund_transaction_id'] = f"REF{random.randint(100000, 999999)}"
    
    logger.info(f"Refund processed: {payment_id}")
    
    return jsonify({
        "success": True,
        **payment
    }), 200

@app.route('/payments/stats', methods=['GET'])
def get_payment_stats():
    """Get payment statistics"""
    completed_payments = [p for p in payments.values() if p['status'] == 'completed']
    failed_payments = [p for p in payments.values() if p['status'] == 'failed']
    refunded_payments = [p for p in payments.values() if p['status'] == 'refunded']
    
    total_revenue = sum(p['amount'] for p in completed_payments)
    refunded_amount = sum(p['amount'] for p in refunded_payments)
    
    # Calculate success rate
    total_attempts = len(completed_payments) + len(failed_payments)
    success_rate = (len(completed_payments) / total_attempts * 100) if total_attempts > 0 else 0
    
    return jsonify({
        "total_payments": len(payments),
        "completed": len(completed_payments),
        "failed": len(failed_payments),
        "refunded": len(refunded_payments),
        "total_revenue": round(total_revenue, 2),
        "refunded_amount": round(refunded_amount, 2),
        "net_revenue": round(total_revenue - refunded_amount, 2),
        "success_rate": round(success_rate, 2),
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    logger.info("Starting Payment Service on port 5002")
    # Disable debug mode in production for better performance
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5002, debug=debug_mode)
