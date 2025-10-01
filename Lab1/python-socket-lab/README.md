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
- Type `quit`, `exit`, or `q` to exit

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

## 📖 Examples

### Example 1: Basic Communication

**Terminal 1 (Server):**
```bash
$ python server.py
INFO:root:Server bound to 127.0.0.1:8080
INFO:root:Server is listening for connections...
INFO:root:Connection established with ('127.0.0.1', 54321)
INFO:root:Received from ('127.0.0.1', 54321): Hello, World!
INFO:root:Sent response to ('127.0.0.1', 54321)
INFO:root:Connection closed with ('127.0.0.1', 54321)
```

**Terminal 2 (Client):**
```bash
$ python client.py
TCP Client - Type 'quit' to exit
----------------------------------------
Enter message to send: Hello, World!
INFO:root:Connected to server at localhost:8080
INFO:root:Sent message: Hello, World!
INFO:root:Received response: Server received at 2025-10-01 14:30:25: Hello, World!
INFO:root:Connection closed
Server response: Server received at 2025-10-01 14:30:25: Hello, World!
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

### Example 3: Multiple Concurrent Clients

You can run multiple client instances simultaneously, and the server will handle them concurrently using separate threads.

## 🔧 Technical Details

### Server Architecture

- **Protocol**: TCP (Transmission Control Protocol)
- **Address**: 127.0.0.1 (localhost)
- **Port**: 8080
- **Concurrency**: Multi-threaded using Python's `threading` module
- **Socket Options**: `SO_REUSEADDR` enabled to avoid "Address already in use" errors

### Client Features

- **Connection Management**: Automatic connection establishment and cleanup
- **Input Modes**: Interactive and command-line argument modes
- **Error Handling**: Graceful handling of connection failures
- **User Experience**: Clear prompts and feedback

### Message Protocol

1. Client establishes TCP connection to server
2. Client sends UTF-8 encoded message
3. Server receives message and processes it
4. Server responds with timestamped message
5. Connection is closed after each message exchange

### Security Considerations

- Server only binds to localhost (127.0.0.1) for security
- No authentication mechanism (suitable for lab/development only)
- No encryption (plain text communication)

## 🐛 Troubleshooting

### Common Issues

1. **"Address already in use" Error**
   - Wait a few seconds and try again
   - The server uses `SO_REUSEADDR` to minimize this issue
   - Kill any existing server processes: `pkill -f server.py`

2. **"Connection refused" Error**
   - Ensure the server is running before starting the client
   - Check if the server is listening on the correct port
   - Verify firewall settings

3. **Import Errors**
   - Ensure you're using Python 3.7+
   - The project uses only standard library modules

4. **Docker Issues**
   - Ensure Docker is running
   - Check port mapping: `-p 8080:8080`
   - For networking issues, try `--network host`

### Debugging

Enable more detailed logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Port Configuration

To use a different port, modify both `server.py` and `client.py`:

```python
PORT = 9090  # Change to desired port
```

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Learning Objectives

This lab demonstrates:

- **Socket Programming**: Basic TCP socket operations
- **Network Communication**: Client-server message exchange
- **Concurrency**: Multi-threaded server handling
- **Error Handling**: Robust network programming practices
- **Logging**: Application monitoring and debugging
- **Containerization**: Docker deployment strategies

## 📄 License

This project is for educational purposes as part of a Distributed Systems course.

---

**Happy Socket Programming! 🚀**
