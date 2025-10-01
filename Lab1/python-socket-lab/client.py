# Import socket library
import socket
import logging
import sys

logging.basicConfig(level=logging.INFO)
HOST = 'localhost'
PORT = 8080

def send_message(message):
    """Send a message to the server and receive response"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        client_socket.connect((HOST, PORT))
        logging.info(f"Connected to server at {HOST}:{PORT}")
        
        client_socket.send(message.encode('utf-8'))
        logging.info(f"Sent message: {message}")
        
        response = client_socket.recv(1024)
        response_message = response.decode('utf-8')
        logging.info(f"Received response: {response_message}")
        
        return response_message
        
    except ConnectionRefusedError:
        logging.error("Could not connect to server. Make sure the server is running.")
        return None
    except Exception as e:
        logging.error(f"Client error: {e}")
        return None
    finally:
        client_socket.close()
        logging.info("Connection closed")

def interactive_client():
    """Interactive client that allows user to send multiple messages"""
    print("TCP Client - Type 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            message = input("Enter message to send: ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not message:
                continue
            
            response = send_message(message)
            if response:
                print(f"Server response: {response}")
            else:
                print("Failed to get response from server")
                
        except KeyboardInterrupt:
            print("\nClient interrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")

def send_single_message(message):
    """Send a single message (useful for testing or scripting)"""
    response = send_message(message)
    if response:
        print(f"Response: {response}")
    else:
        print("Failed to communicate with server")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        send_single_message(message)
    else:
        interactive_client()
