# Personal AI Agent

A Python-based personal assistant that runs in the background to automatically process and respond to emails using local Ollama LLM models.

## Features

- **Gmail Integration**: Automatically checks for unread emails using Gmail API
- **Local LLM Processing**: Uses Ollama for email classification and response generation
- **Smart Email Classification**: Categorizes emails by type, priority, and required actions
- **Automated Responses**: Can create draft replies or auto-send responses for certain email types
- **Background Service**: Runs continuously as a daemon process
- **Safe Mode**: Creates drafts by default, with optional auto-send for safe categories

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create credentials (OAuth 2.0 Client ID for Desktop Application)
5. Download the JSON file and save as `config/gmail_credentials.json`

### 3. Ollama Setup

Install and start Ollama with your preferred model:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (e.g., llama3.2)
ollama pull llama3.2

# Start Ollama service
ollama serve
```

### 4. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. First Run

```bash
# Check system status
python main.py status

# Run once to test and authenticate Gmail
python main.py once

# Start as background daemon
python main.py daemon
```

## Usage

- `python main.py daemon` - Run as background service
- `python main.py once` - Process emails once and exit  
- `python main.py status` - Show system status

## Configuration Options

- `AUTO_SEND_RESPONSES`: Enable automatic sending for safe email categories
- `CHECK_INTERVAL_MINUTES`: How often to check for new emails
- `OLLAMA_MODEL`: Which Ollama model to use for processing
- `MAX_EMAILS_PER_CHECK`: Limit emails processed per cycle

## Email Processing

The assistant will:
1. Check for unread emails every 5 minutes (configurable)
2. Classify each email by category, priority, and required action
3. Generate appropriate responses using the local LLM
4. Create draft replies (or auto-send for safe categories)
5. Mark processed emails as read

## Security

- All processing happens locally using Ollama
- Gmail credentials stored securely using OAuth2
- Auto-send disabled by default for safety
- Comprehensive logging for audit trail