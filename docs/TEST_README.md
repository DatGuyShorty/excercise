# Test Suite for Text Analysis System

## What This Does

The `run_test.py` script tests all the code to make sure it works correctly. It's like a quality check for the program.

## Types of Tests

### **Different Test Categories**
- **Unit Tests**: Test individual functions by themselves
- **Integration Tests**: Test if client and server work together
- **Stress Tests**: Test with lots of data to see if it breaks
- **Hash Tests**: Make sure file checking works
- **Mock Tests**: Test parts in isolation with fake data

### **What Gets Tested**

#### Client Functions (`client.py`)
- Connecting to servers and getting files
- Processing text and counting words
- Handling partial words when data comes in chunks
- Running multiple connections at the same time

#### Server Functions (`server.py`)
- Starting up and sending files
- Making sure files exist before sending
- Calculating hash codes for file verification

## How to Run Tests

### Simple Commands

```bash
# Run all tests
python run_test.py

# Run only unit tests
python run_test.py --mode unit

# Run integration tests
python run_test.py --mode integration

# Run the old-style test
python run_test.py --mode legacy

# See more details
python run_test.py --verbose
```

### What Each Mode Does

| Mode | What It Tests |
|------|---------------|
| `all` | Everything (recommended) |
| `unit` | Individual functions only |
| `integration` | Client-server communication |
| `legacy` | Original test method |

## Test Results

When tests run, you'll see:
- A summary at the end showing total results

## What Each Test Group Does

### ClientUnitTests (10 tests)
Tests the client functions:
- Reading and processing text
- Handling different types of input
- Managing word boundaries
- Counting words correctly

### ServerUnitTests (3 tests)  
Tests the server functions:
- Starting up properly
- Validating files and settings
- Handling network connections

### IntegrationTests (2 tests)
Tests client and server working together:
- Single server connection
- Multiple server connections
- Real file transfers

### Other Tests
- **HashVerificationTests**: Tests file integrity checking
- **StressTests**: Tests with large amounts of data
- **MockTests**: Tests individual pieces with fake data

## When Tests Fail

If tests fail, they'll show:
1. Which test failed
2. What was expected vs what actually happened
3. Error messages explaining the problem

Common issues:
- Files missing (make sure .txt files exist)
- Ports already in use (wait a bit and try again)
- Network problems (check if servers started correctly)

## Adding New Tests

To add tests (for advanced users):
1. Add new test methods to existing test classes
2. Create new test classes that inherit from `BaseTestCase`
3. Add the new class to the test runner list

## Requirements

- Python 3.7 or newer
- The main project files: `client.py`, `server.py`
- Text files: `frankenstein.txt`, `dracula.txt` (for integration tests)

