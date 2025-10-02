import time
import requests
import grpc
from generated import user_service_pb2, user_service_pb2_grpc

def benchmark_rest():
    start = time.time()
    for _ in range(100):
        requests.get("http://localhost:5000/users/1")
    end = time.time()
    return end - start

def benchmark_grpc():
    channel = grpc.insecure_channel("localhost:50051")
    stub = user_service_pb2_grpc.UserServiceStub(channel)
    start = time.time()
    for _ in range(100):
        stub.GetUser(user_service_pb2.UserRequest(id=1))
    end = time.time()
    return end - start

if __name__ == "__main__":
    rest_time = benchmark_rest()
    grpc_time = benchmark_grpc()
    print(f"REST API time: {rest_time:.4f} sec")
    print(f"gRPC time: {grpc_time:.4f} sec")
