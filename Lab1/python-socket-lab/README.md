# Python Socket Lab

A distributed systems lab project demonstrating TCP socket communication between client and server using Python's socket library.

This project implements a basic TCP client-server architecture using Python sockets. The server can handle multiple concurrent client connections using threading, and each client can send messages to receive timestamped responses from the server.


## Project Structure

```
python-socket-lab/
├── server.py
├── client.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Usage
### Running the Server

Start the TCP server on localhost:8080:

```bash
python server.py
```

The server will:
- Bind to `127.0.0.1:8080`
- Listen for incoming connections
- Handle multiple clients concurrently
- Log all activities

Expected output:
```
INFO:root:Server bound to 127.0.0.1:8080
INFO:root:Server is listening for connections...
```


### Running the Client

#### Interactive Mode

Run the client without arguments for interactive mode:

```bash
python client.py
```

This will start an interactive session where you can:
- Type messages to send to the server
- Receive timestamped responses

#### Single Message Mode

Send a single message directly:

```bash
python client.py "Hello, Server!"
```

### Docker Deployment

#### Run Server in Docker

```bash
# Run the server container
docker run -p 8080:8080 python-socket-lab

# Or run in detached mode
docker run -d -p 8080:8080 --name socket-server python-socket-lab
```

#### Run Client

Since the client needs to connect to the server, you can either:

1. **Connect to dockerized server from host:**
   ```bash
   # Modify client.py to use 'localhost' instead of '127.0.0.1'
   python client.py "Hello from host!"
   ```

2. **Run client in another container:**
   ```bash
   docker run -it --network host python-socket-lab python client.py "Hello from container!"
   ```

## Examples

### Example 1: Basic Communication

**Terminal 1 (Server):**
```bash
$ python server.py
INFO:root:Server bound to 127.0.0.1:8080
INFO:root:Server is listening for connections...
INFO:root:Accepted connection from ('127.0.0.1', 53901)
INFO:root:Connection established with ('127.0.0.1', 53901)
INFO:root:Received from ('127.0.0.1', 53901): Hello, Aditya
INFO:root:Sent response to ('127.0.0.1', 53901)
INFO:root:Connection closed with ('127.0.0.1', 53901)
```

**Terminal 2 (Client):**
```bash
$ python client.py
TCP Client - Type 'quit' to exit
----------------------------------------
Enter message to send: Hello, Aditya!
INFO:root:Connected to server at localhost:8080
INFO:root:Sent message: Hello, Aditya!
INFO:root:Received response: Server received at 2025-10-01 23:27:44: Hello, Aditya
INFO:root:Connection closed
Server response: Server received at 2025-10-01 23:27:44: Hello, Aditya
```

### Example 2: Command Line Usage

```bash
$ python client.py "Quick message"
INFO:root:Connected to server at localhost:8080
INFO:root:Sent message: Quick message
INFO:root:Received response: Server received at 2025-10-01 14:31:10: Quick message
INFO:root:Connection closed
Response: Server received at 2025-10-01 14:31:10: Quick message
```


