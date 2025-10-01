FROM python:3.9-slim
WORKDIR /app
COPY *.py .
RUN sed -i "s/HOST = '127.0.0.1'/HOST = '0.0.0.0'/" server.py
EXPOSE 8080
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser
CMD ["python", "server.py"]