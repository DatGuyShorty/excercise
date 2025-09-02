"""
Text File Streaming Server

A TCP server that streams text files to clients with data integrity verification.

This module provides a TCP server that:
- Streams text files to connected clients in configurable chunks
- Calculates and sends SHA-256 hash for data integrity verification
- Supports multiple concurrent client connections
- Logs all operations for monitoring and debugging

Author: Tibor Hoppan
Date: September 2, 2025
"""

import socket
import os
import sys
import hashlib
import logging
import asyncio
from typing import Optional

# Logging configuration - will be set per server instance to avoid conflicts
logger = None

# Configuration constants for server behavior and validation
DEFAULT_CHUNK_SIZE = 8192          # Default network chunk size in bytes for file streaming
DEFAULT_HOST = 'localhost'         # Default hostname for server binding
DEFAULT_PORT = 9001               # Default port number for server listening
SOCKET_LISTEN_BACKLOG = 5         # Maximum number of queued client connections
MAX_PORT_NUMBER = 65535           # Maximum valid TCP port number
MIN_CHUNK_SIZE = 1024             # Minimum allowed chunk size to ensure reasonable performance
MAX_CHUNK_SIZE = 1048576          # Maximum allowed chunk size (1MB) to prevent memory issues

def configure_logging(port: int) -> logging.Logger:
    """
    Configure logging for a specific server instance with port-specific log files.
    
    Creates a unique logger for each server instance to prevent log conflicts
    when multiple servers run simultaneously. Each server gets its own log file
    and console output with consistent formatting.
    
    Args:
        port (int): Server port number used to create unique log filename and logger name
        
    Returns:
        logging.Logger: Configured logger instance with both file and console handlers
        
    Note:
        - Creates logs directory if it doesn't exist
        - Avoids duplicate handlers if logger already exists
        - Uses port number to ensure unique logger names (server_9001, server_9002, etc.)
        - Logs both to file (logs/server_{port}.log) and console for monitoring
        
    Example:
        >>> logger = configure_logging(9001)
        >>> logger.info("Server started")  # Logs to both file and console
    """
    # Ensure logs directory exists for all server instances
    os.makedirs('logs', exist_ok=True)
    
    # Create logger with unique name based on port to prevent conflicts
    logger_name = f"server_{port}"
    server_logger = logging.getLogger(logger_name)
    
    # Avoid duplicate handlers if logger already exists from previous calls
    if server_logger.handlers:
        return server_logger
    
    # Configure logging level for detailed operation tracking
    server_logger.setLevel(logging.INFO)
    
    # Create file handler with port-specific filename for persistent logging
    log_filename = f'logs/server_{port}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler for real-time monitoring and debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create consistent formatter for all log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add both handlers to enable dual logging (file + console)
    server_logger.addHandler(file_handler)
    server_logger.addHandler(console_handler)
    
    return server_logger

def validate_file_path(file_path: str) -> bool:
    """
    Validate file path to prevent directory traversal attacks and ensure file accessibility.
    
    Performs security validation to prevent malicious file access attempts,
    including directory traversal attacks (../../../etc/passwd). Also verifies
    that the file exists and is accessible for reading.
    
    Args:
        file_path (str): File path to validate for security and accessibility
        
    Returns:
        bool: True if path is safe and file is accessible, False otherwise
        
    Security Features:
        - Blocks directory traversal patterns (../, ..\\, etc.)
        - Ensures file exists in the filesystem
        - Verifies path points to a regular file (not directory or special file)
        
    Example:
        >>> validate_file_path("data/frankenstein.txt")  # Safe file
        True
        >>> validate_file_path("../../../etc/passwd")    # Blocked attack
        False
    """
    if not file_path:
        return False
    
    # Check for directory traversal patterns to prevent security attacks
    dangerous_patterns = ['../', '..\\', '../', '..\\\\']
    for pattern in dangerous_patterns:
        if pattern in file_path:
            return False
    
    # Ensure file exists and is accessible
    if not os.path.exists(file_path):
        return False
    
    # Verify path points to a regular file (not directory or special file)
    if not os.path.isfile(file_path):
        return False
        
    return True

def validate_arguments(host: str, port: int, chunk_size: int, file_path: str) -> tuple[bool, str]:
    """
    Validate all command line arguments for server configuration.
    
    Performs comprehensive validation of server startup parameters to ensure
    safe and efficient operation. Checks network parameters, performance settings,
    file accessibility, and security constraints.
    
    Args:
        host (str): Hostname or IP address to bind server to
        port (int): TCP port number for server listening
        chunk_size (int): Data chunk size in bytes for file streaming
        file_path (str): Path to file that will be served to clients
        
    Returns:
        tuple[bool, str]: (is_valid, error_message) where error_message is empty if valid
        
    Validation Rules:
        - Port: Must be in valid TCP range (1-65535)
        - Chunk size: Must be between 1KB-1MB for optimal performance
        - File path: Must pass security validation and exist
        - Host: Must not be empty string
        
    Example:
        >>> is_valid, msg = validate_arguments("localhost", 9001, 8192, "data/test.txt")
        >>> if not is_valid:
        ...     print(f"Error: {msg}")
    """
    # Validate port number is in valid TCP range
    if not (1 <= port <= MAX_PORT_NUMBER):
        return False, f"Port must be between 1 and {MAX_PORT_NUMBER}"
    
    # Validate chunk size for optimal performance and memory usage
    if not (MIN_CHUNK_SIZE <= chunk_size <= MAX_CHUNK_SIZE):
        return False, f"Chunk size must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}"
    
    # Validate file path for security and accessibility
    if not validate_file_path(file_path):
        return False, f"Invalid or inaccessible file path: {file_path}"
    
    # Validate host parameter is not empty
    if not host or len(host.strip()) == 0:
        return False, "Host cannot be empty"
    
    return True, ""

async def handle_client(client_socket: socket.socket, addr: tuple, file_path: str, chunk_size: int, logger: logging.Logger) -> None:
    """
    Handle a single client connection asynchronously with complete file streaming.
    
    Manages the complete client interaction lifecycle: file size transmission,
    chunked file content streaming, hash calculation, and integrity verification.
    Uses async I/O to prevent blocking other client connections.
    
    Protocol Sequence:
    1. Send file size as UTF-8 string terminated by newline
    2. Stream file content in chunks of specified size
    3. Send SHA-256 hash with HASH: prefix for integrity verification
    
    Args:
        client_socket: Connected TCP socket for this specific client
        addr: Client address tuple (IP, port) for logging identification
        file_path: Absolute or relative path to file being served
        chunk_size: Size in bytes for each data chunk sent to client
        logger: Logger instance for tracking client interactions
        
    Note:
        - Automatically closes client socket when done or on error
        - Calculates rolling hash during streaming for efficiency
        - Uses asyncio event loop for non-blocking socket operations
        - Logs successful transfers and any errors encountered
    """
    try:
        # Get asyncio event loop for non-blocking socket operations
        loop = asyncio.get_event_loop()
        
        # Send file size first as part of the communication protocol
        file_size = os.path.getsize(file_path)
        message = f"{file_size}\n".encode('utf-8')
        await loop.sock_sendall(client_socket, message)
        
        # Initialize rolling hash for real-time integrity calculation
        rolling_hash = hashlib.sha256()
        
        # Stream file content in chunks for memory efficiency
        bytes_sent = 0
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                # Update hash calculation with each chunk
                rolling_hash.update(chunk)
                # Send chunk using async I/O to prevent blocking
                await loop.sock_sendall(client_socket, chunk)
                bytes_sent += len(chunk)
        
        # Send integrity hash after file content with protocol framing
        file_hash = rolling_hash.hexdigest()
        hash_message = f"\nHASH:{file_hash}\n".encode('utf-8')
        await loop.sock_sendall(client_socket, hash_message)
        
        # Log successful transfer for monitoring and debugging
        logger.info(f"Server sent {bytes_sent} bytes to {addr}")
        logger.debug(f"Server calculated hash: {file_hash}")

    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}")
    finally:
        # Ensure client socket is always closed to free resources
        try:
            client_socket.close()
        except Exception as e:
            logger.error(f"Error closing client socket {addr}: {e}")

async def server(host: str, port: int, chunk_size: int, file_path: str, logger: logging.Logger) -> None:
    """
    Start an async TCP server that streams a text file to clients.
    
    The server sends the file size first, then streams the file content in chunks,
    and finally sends a SHA-256 hash for data integrity verification.
    Handles multiple concurrent client connections.
    
    Args:
        host (str): The hostname or IP address to bind the server to (e.g., 'localhost')
        port (int): The port number to listen on (e.g., 9001)
        chunk_size (int): The size of data chunks to read/send in bytes (e.g., 8192)
        file_path (str): Path to the text file to stream (e.g., 'frankenstein.txt')
        logger (logging.Logger): Logger instance for this server
    
    Raises:
        OSError: If the server cannot bind to the specified host/port
        FileNotFoundError: If the specified file_path does not exist
        KeyboardInterrupt: When the server is manually stopped with Ctrl+C
    
    Note:
        The server runs indefinitely until stopped with KeyboardInterrupt.
        Each client connection is handled concurrently using asyncio.
        
    Example:
        >>> logger = configure_logging(9001)
        >>> await server('localhost', 9001, 8192, 'frankenstein.txt', logger)
        Server for frankenstein.txt listening on localhost:9001
    """
    server_socket: Optional[socket.socket] = None
    try:
        # Create and configure TCP socket for server listening
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(SOCKET_LISTEN_BACKLOG)
        server_socket.setblocking(False)  # Enable non-blocking mode for async operations
        
        # Announce server startup to console and logs
        print(f"Server for {file_path} listening on {host}:{port}")
        logger.info(f"Server for {file_path} listening on {host}:{port}")
        
        # Main server loop - accept and handle client connections
        while True:
            try:
                # Accept new client connections asynchronously
                client_socket, addr = await asyncio.get_event_loop().sock_accept(server_socket)
                # Handle each client concurrently without blocking others
                asyncio.create_task(handle_client(client_socket, addr, file_path, chunk_size, logger))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print(f"\nServer on port {port} shutting down...")
        logger.info(f"Server on port {port} shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Ensure server socket is always closed to free port
        if server_socket:
            try:
                server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")

if __name__ == "__main__":
    """
    Main entry point for the text file streaming server.
    
    Parses command line arguments and starts the server with the specified configuration.
    
    Command line usage:
        python server.py <host> <port> <chunk_size> <file_path>
    
    Args (from command line):
        host: Hostname or IP address to bind to
        port: Port number to listen on
        chunk_size: Size of data chunks in bytes
        file_path: Path to the text file to serve
        
    Example:
        python server.py localhost 9001 8192 frankenstein.txt
    """
    if len(sys.argv) != 5:
        print("Usage: python server.py <host> <port> <chunk_size> <file_path>")
        print("Example: python server.py localhost 9001 8192 frankenstein.txt")
        sys.exit(1)
    
    # Parse command line arguments with error handling
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        chunk_size = int(sys.argv[3])
        file_path = sys.argv[4]
    except ValueError as e:
        print(f"Error: Invalid numeric argument - {e}")
        sys.exit(1)

    # Validate all arguments before starting server
    is_valid, error_message = validate_arguments(host, port, chunk_size, file_path)
    if not is_valid:
        print(f"Error: {error_message}")
        sys.exit(1)

    # Configure logging system for this server instance
    logger = configure_logging(port)
    logger.info(f"Starting server on {host}:{port} for file {file_path}")

    # Start the async server with comprehensive error handling
    try:
        asyncio.run(server(host, port, chunk_size, file_path, logger))
    except Exception as e:
        print(f"Server error: {e}")
        logger.error(f"Server error: {e}")
        sys.exit(1)