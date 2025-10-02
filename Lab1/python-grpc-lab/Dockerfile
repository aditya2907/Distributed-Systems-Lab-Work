FROM python:3.9-slim
WORKDIR /python-grpc-lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proto/ ./proto/
RUN mkdir -p generated
RUN python -m grpc_tools.protoc -I./proto --python_out=./generated --grpc_python_out=./generated proto/user_service.proto
RUN sed -i 's/import user_service_pb2/from . import user_service_pb2/g' generated/user_service_pb2_grpc.py
COPY *.py .
RUN touch generated/__init__.py
EXPOSE 50051
CMD ["python", "server.py"]