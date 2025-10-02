# Python REST API Lab

A simple REST API built with Flask for learning distributed systems concepts.

This project demonstrates the implementation of a RESTful web service using Flask. It provides basic CRUD (Create, Read, Update, Delete) operations for user management through HTTP endpoints.

## Project Structure

```
python-rest-api-lab/
├── app.py          # Main Flask application with API endpoints
├── model.py        # User model definition
├── README.md       # Project documentation
└── __pycache__/    # Python bytecode cache
```


## Installation

1. Navigate to the project directory:
   ```bash
   cd python-rest-api-lab
   ```

2. Install Flask (if not already installed):
   ```bash
   pip install flask
   ```

## Usage

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. The server will start on `http://localhost:5000`

3. Test the API endpoints using curl, Postman, or any HTTP client:
