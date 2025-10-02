import grpc
from concurrent import futures
import time

from generated import user_service_pb2, user_service_pb2_grpc

# Temp DB
users = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}

class UserService(user_service_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = users.get(request.id)
        if not user:
            context.set_details("User not found")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return user_service_pb2.UserResponse()
        return user_service_pb2.UserResponse(**user)

    def CreateUser(self, request, context):
        new_id = max(users.keys()) + 1
        users[new_id] = {"id": new_id, "name": request.name, "email": request.email}
        return user_service_pb2.UserResponse(**users[new_id])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    print("gRPC Server running on port 50051")
    server.start()
    try:
        while True:
            time.sleep(86400)  # keep alive
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
