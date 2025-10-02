# Python gRPC Lab

A distributed systems lab project demonstrating gRPC communication between client and server using Python and Protocol Buffers.

This project implements a gRPC-based User Service that provides user management functionality through high-performance, language-neutral remote procedure calls.

## Project Structure

```
python-grpc-lab/
├── proto/
│   └── user_service.proto      # Protocol Buffer definitions
├── generated/
│   ├── __init__.py
│   ├── user_service_pb2.py     # Generated Protocol Buffer classes
│   └── user_service_pb2_grpc.py # Generated gRPC service classes
├── server.py                   # gRPC server implementation
├── client.py                   # gRPC client implementation
├── benchmark.py                # Performance comparison tool
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .dockerignore              # Docker ignore rules
└── README.md                   # This file
```


## Installation

1. Navigate to the project directory:
   ```bash
   cd Lab1/python-grpc-lab
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate gRPC code from Protocol Buffer definitions:
   ```bash
   python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated proto/user_service.proto
   ```

4. Create `__init__.py` in the generated directory:
   ```bash
   touch generated/__init__.py
   ```

## Usage

### Running the gRPC Server

Start the gRPC server on localhost:50051:

```bash
python server.py
```

Expected output:
```
gRPC Server running on port 50051
```

### Running the gRPC Client

In a separate terminal, run the client to test the service:

```bash
python client.py
```

Expected output:
```
GetUser Response: id: 2
name: "Bob"
email: "bob@example.com"

CreateUser Response: id: 3
name: "Charlie"
email: "charlie@example.com"
```

### Performance Benchmarking

Compare gRPC performance with REST API (requires REST API server running on port 5000):

```bash
python benchmark.py
```

## API Reference

The gRPC service provides two main operations:

### GetUser
- **Method**: `GetUser(UserRequest) returns (UserResponse)`
- **Description**: Retrieves a user by ID
- **Request**: `UserRequest` with `id` field
- **Response**: `UserResponse` with `id`, `name`, and `email` fields

### CreateUser
- **Method**: `CreateUser(CreateUserRequest) returns (UserResponse)`
- **Description**: Creates a new user
- **Request**: `CreateUserRequest` with `name` and `email` fields
- **Response**: `UserResponse` with generated `id`, `name`, and `email` fields

## Docker Deployment

### Build the Docker Image

```bash
docker build -t python-grpc-lab .
```

### Run the Server Container

```bash
# Run in foreground
docker run -p 50051:50051 python-grpc-lab

# Run in background
docker run -d -p 50051:50051 --name grpc-server python-grpc-lab
```

### Run Client Against Dockerized Server

```bash
# Modify client.py to connect to localhost:50051, then run:
python client.py

# Or run client in container
docker run -it --network host python-grpc-lab python client.py
```

### Custom Client Usage

```python
GetUser Response: id: 2
name: "Bob"
email: "bob@example.com"

CreateUser Response: id: 3
name: "Charlie"
email: "charlie@example.com"

```

### 3: Performance Comparison

```bash
$ python benchmark.py
REST API time: 0.1411 sec
gRPC time: 0.0.0170 sec
```

## Protocol Buffer Schema

The service uses the following Protocol Buffer definitions from [`user_service.proto`](Lab1/python-grpc-lab/proto/user_service.proto):

```protobuf
// User message
message User {
    int32 id = 1;
    string name = 2;
    string email = 3;
}

// Service definition
service UserService {
    rpc GetUser(UserRequest) returns (UserResponse);
    rpc CreateUser(CreateUserRequest) returns (UserResponse);
}
```

