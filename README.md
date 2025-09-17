# SOAP Injector

A Python tool for injecting SOAP messages with automatic variable substitution. This tool allows you to send randomized SOAP messages to test endpoints with dynamic content generation.

## Features

- 🎲 **Random Template Selection**: Automatically selects random SOAP templates from a directory
- 🔄 **Variable Substitution**: Dynamic replacement of variables with UUIDs, timestamps, and random values
- 📊 **Batch Processing**: Send multiple messages with configurable delays
- 📝 **Detailed Logging**: Comprehensive logging with success/failure statistics
- ⚙️ **Configurable**: Customizable timeouts, delays, and template directories

## Quick Start

### 1. Setup Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install requests
```

### 2. Run the Injector

```bash
# Send a single SOAP message
python soap_injector.py http://localhost:10000/soap-endpoint

# Send multiple messages with delay
python soap_injector.py http://localhost:10000/soap-endpoint --count 10 --delay 1.0

# Use custom template directory
python soap_injector.py http://localhost:10000/soap-endpoint --soap-dir ./my_templates
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `endpoint` | - | SOAP endpoint URL (required) | - |
| `--soap-dir` | `-d` | Directory containing SOAP templates | `./soap_templates` |
| `--count` | `-c` | Number of messages to send | `1` |
| `--delay` | `-w` | Delay between sends (seconds) | `0.0` |
| `--timeout` | `-t` | HTTP request timeout (seconds) | `30` |
| `--verbose` | `-v` | Enable verbose logging | `false` |

## SOAP Templates

Place your SOAP XML templates in the `soap_templates/` directory. The tool supports variable substitution using the `{{VARIABLE_NAME}}` syntax.

### Supported Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{UUID}}` | Standard UUID v4 | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `{{UUID_UPPER}}` | Uppercase UUID | `F47AC10B-58CC-4372-A567-0E02B2C3D479` |
| `{{UUID_NO_DASH}}` | UUID without dashes | `f47ac10b58cc4372a5670e02b2c3d479` |
| `{{TIMESTAMP}}` | ISO timestamp | `2025-09-17T14:30:15` |
| `{{TIMESTAMP_MS}}` | Timestamp with milliseconds | `2025-09-17T14:30:15.123` |
| `{{DATE}}` | Current date | `2025-09-17` |
| `{{TIME}}` | Current time | `14:30:15` |
| `{{EPOCH}}` | Unix timestamp | `1726578615` |
| `{{RANDOM_ID}}` | 6-digit random number | `482751` |
| `{{RANDOM_ALPHA}}` | 8-character random string | `HXMKPQWZ` |
| `{{RANDOM_ALPHANUM}}` | 10-character alphanumeric | `H3X9MK2QWZ` |

### Example Template

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns:Request xmlns:ns="http://example.com/service">
      <ns:MessageId>MSG-{{UUID}}</ns:MessageId>
      <ns:Timestamp>{{TIMESTAMP}}</ns:Timestamp>
      <ns:TransactionId>TXN_{{RANDOM_ID}}</ns:TransactionId>
      <ns:Data>
        <ns:Reference>REF_{{UUID_NO_DASH}}</ns:Reference>
        <ns:UserId>USER_{{RANDOM_ALPHANUM}}</ns:UserId>
      </ns:Data>
    </ns:Request>
  </soap:Body>
</soap:Envelope>
```

## Project Structure

```text
soap-injector/
├── soap_injector.py          # Main script
├── soap_templates/           # SOAP template directory
│   ├── message-1.xml        # Example template 1
│   └── message-2.xml        # Example template 2
├── .venv/                   # Python virtual environment
└── README.md                # This file
```

## Usage Examples

### Basic Usage

```bash
# Send one random message
python soap_injector.py http://localhost:8080/soap

# Send 5 messages with 2-second delays
python soap_injector.py http://localhost:8080/soap --count 5 --delay 2

# Use verbose logging
python soap_injector.py http://localhost:8080/soap --verbose
```

### Load Testing

```bash
# Send 100 messages as fast as possible
python soap_injector.py http://localhost:8080/soap --count 100

# Send 50 messages with 0.5s delay (sustained load)
python soap_injector.py http://localhost:8080/soap --count 50 --delay 0.5

# Long timeout for slow endpoints
python soap_injector.py http://localhost:8080/soap --timeout 60
```

## Development Setup

1. **Clone/Setup the project**:

   ```bash
   cd soap-injector
   ```

2. **Create virtual environment**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install requests
   ```

4. **Add your SOAP templates**:
   - Place XML files in `soap_templates/` directory
   - Use `{{VARIABLE_NAME}}` syntax for dynamic content

5. **Test the setup**:

   ```bash
   python soap_injector.py --help
   ```

## Output and Logging

The tool provides detailed logging including:

- ✅ **Success messages**: HTTP 200 responses with response size
- ❌ **Error messages**: HTTP errors, timeouts, connection issues
- 📊 **Statistics**: Success rate and timing information for batch runs

Example output:

```text
2025-09-17 14:39:05 [INFO] Chargé 2 fichier(s) SOAP depuis soap_templates
2025-09-17 14:39:05 [INFO]   - message-2.xml
2025-09-17 14:39:05 [INFO]   - message-1.xml
2025-09-17 14:39:05 [INFO] Envoi SOAP [message-1.xml] vers http://localhost:10000/soap-endpoint
2025-09-17 14:39:05 [INFO] ✓ Succès [message-1.xml] - HTTP 200 - 785 bytes
```

## Troubleshooting

### Common Issues

1. **Import Error**: `ModuleNotFoundError: No module named 'requests'`

   ```bash
   # Make sure virtual environment is activated and requests is installed
   source .venv/bin/activate
   pip install requests
   ```

2. **No SOAP files found**:

   ```bash
   # Check that XML files exist in soap_templates directory
   ls soap_templates/*.xml
   ```

3. **Connection refused**:

   ```bash
   # Verify the SOAP endpoint is running and accessible
   curl -X POST http://localhost:10000/soap-endpoint
   ```

### Debug Mode

Use `--verbose` flag to enable debug logging for troubleshooting:

```bash
python soap_injector.py http://localhost:8080/soap --verbose
```

## License

This project is provided as-is for testing and development purposes.
