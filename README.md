# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Prerequisites

- Python 3.9+
- GCP CLI ([install guide](https://cloud.google.com/sdk/docs/install))
- Vertex AI User role on GCP project `dev-app-286019`

## Setup

### Step 1: Get GCP Access

Ask Evan Trippler or Christopher Bello to grant you the Vertex AI User role:

```bash
gcloud projects add-iam-policy-binding dev-app-286019 \
  --member="user:YOUR_EMAIL@coalesce.io" \
  --role="roles/aiplatform.user"
```

### Step 2: Authenticate with GCP

```bash
gcloud auth application-default login
```

This opens a browser — sign in with your `@coalesce.io` account. No Anthropic API key is needed; authentication is handled through your GCP credentials.

### Step 3: Configure the environment variables

Create or edit the `.env` file in the project root:

```
CLAUDE_MODEL="claude-sonnet-4-6"
GCP_PROJECT_ID="dev-app-286019"
GCP_REGION="us-east5"
```

### Step 4: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install "anthropic[vertex]" python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

3. Run the project

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Linting and Typing Check

There are no lint or type checks implemented.

## Troubleshooting

- **404 / "model not found"** — Re-run `gcloud auth application-default login` and try again. If it persists, confirm your account has the Vertex AI User role on `dev-app-286019`.
- **"quota exceeded" warning** — This is just a warning and can be ignored. If you hit actual quota issues, run: `gcloud auth application-default set-quota-project dev-app-286019`
- **Credentials expire** — ADC tokens refresh automatically, but if you see auth errors after a long time, re-run `gcloud auth application-default login`.
