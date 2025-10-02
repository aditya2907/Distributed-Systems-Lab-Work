import grpc
from generated import user_service_pb2, user_service_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)

        # Test GetUser
        try:
            response = stub.GetUser(user_service_pb2.UserRequest(id=2))
            print(f"GetUser Response: {response}")
        except grpc.RpcError as e:
            print(f"Error: {e.code()} - {e.details()}")

        # Test CreateUser
        response = stub.CreateUser(user_service_pb2.CreateUserRequest(name="Charlie", email="charlie@example.com"))
        print(f"CreateUser Response: {response}")

if __name__ == "__main__":
    run()
