FROM python:3.9-slim
WORKDIR /python-socket-lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
RUN sed -i "s/HOST = '127.0.0.1'/HOST = '0.0.0.0'/" server.py
EXPOSE 8080
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /python-socket-lab
USER appuser
CMD ["python", "server.py"]