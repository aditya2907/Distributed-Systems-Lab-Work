# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory in container
WORKDIR /python-grpc-lab

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and generate gRPC code
COPY proto/ ./proto/
RUN mkdir -p generated
RUN python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated proto/user_service.proto

# Fix the import issue in generated gRPC file
RUN sed -i 's/import user_service_pb2/from . import user_service_pb2/g' generated/user_service_pb2_grpc.py

# Copy all Python files (server, client, benchmark)
COPY *.py .

# Create __init__.py files to make generated a proper Python package
RUN touch generated/__init__.py

# Expose the gRPC port
EXPOSE 50051

# Run the server by default
CMD ["python", "server.py"]