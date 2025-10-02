from flask import Flask, jsonify, request
from model import User

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the REST API!"

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.get_all()
    return jsonify(users), 200

@app.route('/api/users/<id>', methods=['GET'])
def get_user(id):
    user = User.get_by_id(id)
    if user:
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not "username" in data or not "email" in data:
        return jsonify({"error": "Invalid user data"}), 400
    user_id = User.create(data)
    return jsonify({"id": user_id, "message": "User created"}), 201

@app.route('/api/users/<id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    updated = User.update(id, data)
    if updated:
        return jsonify({"message": "User updated"}), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users/<id>', methods=['DELETE'])
def delete_user(id):
    deleted = User.delete(id)
    if deleted:
        return jsonify({"message": "User deleted"}), 200
    return jsonify({"error": "User not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
