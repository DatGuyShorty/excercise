## Main Files

This project has three main Python files:

### server.py
- Runs a server that sends text files to clients
- Checks files with hash codes to make sure they're not broken
- Can talk to multiple clients at the same time

### client.py
- Connects to servers and gets text files
- Counts how many times each word appears
- Can connect to multiple servers at once

### run_test.py
- Tests if everything works correctly
- Starts servers and clients, checks if they work

## How to See More Info

Use Python's built-in help:

```bash
python -c "import server; help(server)"
python -c "import client; help(client)"
```

Or check function docs:
```python
import server
print(server.server.__doc__)
```

## Notes
- All functions have help text that explains what they do
- Error messages will tell you what went wrong
- Log files show what happened when the programs ran
