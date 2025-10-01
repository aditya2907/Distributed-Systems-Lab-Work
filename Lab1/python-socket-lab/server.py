# Import socket library
import socket
import threading
import time
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
HOST = '127.0.0.1'
PORT = 8080

def handle_client(client_socket, client_address):
    try:
        logging.info(f"Connection established with {client_address}")
        
        data = client_socket.recv(1024)
        if data:
            message = data.decode('utf-8')
            logging.info(f"Received from {client_address}: {message}")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response = f"Server received at {timestamp}: {message}"
            
            client_socket.send(response.encode('utf-8'))
            logging.info(f"Sent response to {client_address}")
        
    except Exception as e:
        logging.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        logging.info(f"Connection closed with {client_address}")

def start_server():
    """Start the TCP server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        logging.info(f"Server bound to {HOST}:{PORT}")
        
        server_socket.listen(5)
        logging.info("Server is listening for connections...")
        
        while True:
            client_socket, client_address = server_socket.accept()
            logging.info(f"Accepted connection from {client_address}")
            
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server_socket.close()
        logging.info("Server socket closed")

if __name__ == "__main__":
    start_server()