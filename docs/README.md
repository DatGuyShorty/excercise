# Text File Analysis Client-Server

A simple program that reads text files over the network and counts words.

## What it does

- **Server**: Sends text files to clients over TCP
- **Client**: Gets files from multiple servers and counts words
- **Hash check**: Makes sure files aren't corrupted during transfer
- **Results**: Shows the 5 most common words

## How to run it

### Quick start (default servers)

1. **Start servers** (in separate terminals):
```bash
python server.py localhost 9001 8192 data/frankenstein.txt
python server.py localhost 9002 8192 data/dracula.txt
```

2. **Run client** (connects to default servers):
```bash
python client.py
```

### Custom server configuration

You can specify which servers to connect to:

**Single server:**
```bash
python client.py localhost:9001
```

**Multiple servers:**
```bash
python client.py localhost:9001,localhost:9002
python client.py 127.0.0.1:9001,127.0.0.1:9002,127.0.0.1:9003
```

**Get help:**
```bash
python client.py --help
```

## Files explained

- `server.py` - Sends files to clients
- `client.py` - Gets files and counts words
- `data/*.txt` - Text files to analyze
- `logs/*.log` - Program logs
- `tests/*.py` - Testing scripts and modules
`run_test.py` - Test runner (Entry point)