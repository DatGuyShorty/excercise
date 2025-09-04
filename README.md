# Text Processing Server-Client System

A Python TCP server-client system for word frequency analysis.

## Overview

This system consists of two main components:
- **server.py** - Asynchronous TCP server that serves text files to clients
- **client.py** - TCP client that processes text data from servers and counts word frequencies

## Project Structure

```
├── server.py              # TCP server for serving text files
├── client.py              # TCP client for text processing
├── data/                   # Text files for processing
├── logs/                   # Application logs
│   ├── client.log
│   └── server.log
└── .venv/                  # Virtual environment
```

## Setup

1. Clone the repository
2. Set up virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

## Usage

### Running the Server

```bash
python server.py <host> <port> <chunk_size> <file_path>
```

Example:
```bash
python server.py localhost 9001 8192 data/frankenstein.txt
python server.py localhost 9002 8192 data/dracula.txt
```

### Running the Client

```bash
python client.py
```

The client connects to servers on localhost:9001 and localhost:9002 by default.

## Architecture

### Server
- Uses asyncio for handling concurrent client connections
- Streams file content in configurable chunks
- Sends file size before content transmission

### Client
- Connects to multiple servers simultaneously
- Processes text streams and counts word frequencies
- Aggregates results from all connected servers

## Error Handling

The system handles:
- Network connection failures
- File not found errors
- UTF-8 encoding issues at chunk boundaries
- Server unavailability

## Logging

Logs are written to:
- `logs/server.log` - Server operations and client connections
- `logs/client.log` - Client operations and processing status
