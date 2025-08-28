# Web-Scout: AI-Powered Search with LLM Summarization

A FastAPI application that performs web searches using DuckDuckGo and generates AI-powered summaries using Google's Gemini AI.

## Features

- Web search using DuckDuckGo
- AI summarization using Gemini 2.5 Flash
- Two output modes: Summary and Detailed analysis
- Docker & Docker Compose ready
- Secure API key management via environment variables

## Prerequisites

- Docker and Docker Compose installed
- Google Gemini API key

## Setup

1. **Clone the repository** (or navigate to your project directory)

2. **Add your Gemini API key** to the `.env` file:
   ```bash
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

3. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

## API Usage

The application will be available at `http://localhost:8000`

### Health Check
```bash
curl http://localhost:8000/health
```

### Search Endpoint

#### Summary Mode (Default)
```bash
curl "http://localhost:8000/search?query=artificial+intelligence"
# or explicitly specify mode=0
curl "http://localhost:8000/search?query=artificial+intelligence&mode=0"
```

#### Detailed Mode
```bash
curl "http://localhost:8000/search?query=artificial+intelligence&mode=1"
```

#### Response Format
```json
{
  "query": "your search query",
  "mode": 0,
  "summary": "AI-generated analysis...",
  "sources_used": 10
}
```

}
```

## MCP Server Integration

Web-Scout can also function as an MCP (Model Context Protocol) server, allowing AI assistants to perform web searches directly through tools.

### MCP Features

- **Web Search Tool**: Perform web searches with AI summarization
- **Dual Mode Support**: Both summary and detailed analysis modes
- **Stdio Transport**: Uses standard input/output for communication
- **JSON Responses**: Structured output for easy integration

### MCP Tools Available

#### Web Search Tool
- **Name**: `web_search`
- **Description**: Perform a web search using DuckDuckGo and generate AI-powered summaries
- **Parameters**:
  - `query` (string, required): The search query to perform
  - `mode` (string, optional): Response mode - "summary" or "detailed" (default: "summary")

### MCP Server Setup

#### Method 1: Direct Python Execution
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:
```bash
export GEMINI_API_KEY=your_api_key_here
```

3. Run the MCP server:
```bash
python mcp_server.py
```

#### Method 2: Docker Container
```bash
# Run as MCP server in Docker
docker run -e GEMINI_API_KEY=your_api_key_here web-scout python main.py --mcp
```

### Integrating with AI Tools

To use Web-Scout as an MCP server with AI tools like Claude Desktop or Roo:

1. **Create MCP Configuration**:
```json
{
  "mcpServers": {
    "web-scout": {
      "command": "python",
      "args": ["/path/to/Web-Scout/mcp_server.py"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

2. **Configure your AI tool** to use the MCP configuration:
   - For Claude Desktop: Add to `~/Library/Application Support/Claude/claude_desktop_config.json`
   - For Roo: Add to the appropriate configuration file

3. **Usage Example**:
```
Can you search for the latest news about artificial intelligence?
```

The AI tool will use the Web-Scout MCP server to perform the search and provide summarized results.

## Development
## Development

### Local Development (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY=your_api_key_here

# Run the application
uvicorn main:app --reload
```

### Using Docker Compose
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the application
docker-compose down

# View logs
docker-compose logs -f web-scout
```

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Docker Configuration
- **Port**: 8000
- **Container name**: web-scout
- **Health check**: Automatic health monitoring

## Security Notes

- The `.env` file is ignored by Git and should never be committed
- API keys are mounted securely via Docker Compose volumes
- The application uses health checks for monitoring

## Error Handling

- Returns proper HTTP status codes
- Includes detailed error messages
- Handles missing API keys and invalid parameters gracefully