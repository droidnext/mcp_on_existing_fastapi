# 🚀 FastAPI MCP Application

A production-ready FastAPI application with Model Context Protocol (MCP) integration for AI tools such as movie recommendation and search.

This repo demonstrates integrating MCP tools into an existing FastAPI application with enterprise-grade features including JWT authentication, comprehensive error handling, structured logging, and extensive test coverage.

## 📚 Resources
- [Medium article on Integrating MCP into exisitng FastAPI application ](https://medium.com/@droidnext/integrating-model-context-protocol-mcp-into-existing-apis-c737d6587d12)
  - Full URL: https://medium.com/@droidnext/integrating-model-context-protocol-mcp-into-existing-apis-c737d6587d12

---

## 🧰 Features

- ⚡ **FastAPI backend** with MCP integration
- 🎬 **Movie recommendation and search tools** via MCP
- 🔐 **JWT authentication** (configurable, supports JWKS)
- 🛠️ **Environment-specific YAML configurations**
- 📊 **Structured logging** with request ID tracking
- 🏥 **Health check endpoints** (`/health`, `/ready`)
- 🧪 **Comprehensive test suite** for MCP tools
- 🐳 **Docker support** (production & development)
- 🔒 **Production-ready** with security hardening
- 📦 **MCP Resources and Prompts** support

---

## 📦 Prerequisites

- **Python 3.10+** (required for type hints and async features)
- **Node.js 14+** (optional, for MCP inspector)
- **Docker** (optional, for containerized deployment)
- [`uv`](https://github.com/astral-sh/uv) (optional, for Python dependency management)

---

## 🧑‍💻 Installation

### Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

## 🛠️ Setup Instructions

Set up the development environment:

```bash
uv init
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt


Install MCP inspector:
```bash
npm install @modelcontextprotocol/inspector
```

## ⚙️ Configuration

The application uses environment-specific YAML configuration files in the `config` directory:

- `app_config.yaml`: Base configuration
- `app_config.dev.yaml`: Development settings
- `app_config.prod.yaml`: Production settings

You can override settings using environment variables or a `.env` file.

### Configuration Structure

```yaml
project:
  name: "FastAPI MCP Application"
  version: "1.0.0"

server:
  allowed_hosts:
    - "http://localhost:8000"

mcp:
  tool_timeout: 60  # seconds
  transport: "streamable-http"  # Options: "streamable-http", "stdio"

auth:
  enable_jwt: false  # Enable/disable JWT authentication
  secret_key: ""  # Optional if using JWKS, required for symmetric algorithms
  algorithm: "HS256"  # Default algorithm (fallback if not in token header)
  allowed_algorithms:  # List of allowed algorithms for validation
    - "HS256"
    - "RS256"
```

### Key Configuration Options

#### Environment Variables

- `APP_ENV`: Set to `'dev'` or `'prod'` to use different configurations
- `ENABLE_JWT`: Toggle JWT authentication (`true`/`false`)
- `ENABLE_ELICITATION`: Enable MCP elicitation features (`true`/`false`)
- `JWT_SECRET_KEY`: JWT secret key (optional if using JWKS)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

#### JWT Configuration

**Symmetric Algorithms (HS256/HS384/HS512):**
```yaml
auth:
  enable_jwt: true
  secret_key: "your-secret-key-here"  # Required
  algorithm: "HS256"
```

**Asymmetric Algorithms with JWKS (RS256/ES256):**
```yaml
auth:
  enable_jwt: true
  secret_key: ""  # Optional - tokens use 'jku' header to fetch public keys
  allowed_algorithms: ["RS256", "ES256"]
```

**Mixed (Support Both):**
```yaml
auth:
  enable_jwt: true
  secret_key: "fallback-secret-for-hs256"  # Used if token has no 'jku'
  allowed_algorithms: ["HS256", "RS256", "ES256"]
```

#### MCP Transport Options

- `streamable-http` (default): HTTP-based transport for web APIs
- `stdio`: Standard I/O transport for CLI/integrated applications

## 🚀 Running the Application

### Using Docker (Recommended)

**Production:**
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Development (with hot reload):**
```bash
# Run development service
docker-compose --profile dev up app-dev

# Or use Dockerfile.dev directly
docker build -f Dockerfile.dev -t fastapi-mcp-app:dev .
docker run -p 8000:8000 -v $(pwd):/app fastapi-mcp-app:dev
```

**Environment Variables:**
```bash
# Set environment variables in .env or docker-compose.yml
ENABLE_ELICITATION=true
ENABLE_JWT=false
JWT_SECRET_KEY=your-secret-key
```

### Using Python Directly

1. Start the FastAPI server:
```bash
# Development
APP_ENV=dev python -m uvicorn app.main:app --reload

# Production
APP_ENV=prod python -m uvicorn app.main:app
```

2. Start the MCP inspector:
```bash
npx @modelcontextprotocol/inspector node build/index.js
```

## 📡 API Endpoints

### Health & Status
- `GET /health` - Health check endpoint (returns service status)
- `GET /ready` - Readiness check endpoint (for Kubernetes orchestration)
- `GET /routes` - List all available routes

### Movie API
- `GET /api/v1/movies` - Movie-related REST API endpoints

### MCP Endpoints
- `POST /mcp` - MCP tools endpoint (JSON-RPC 2.0)
- `POST /mcp/elicitation` - MCP elicitation endpoint (optional, requires `ENABLE_ELICITATION=true`)

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI, disabled in production)
- `GET /redoc` - Alternative API documentation (ReDoc, disabled in production)

## 🛠️ MCP Tools

The application provides the following MCP tools (per [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)):

### Available Tools

- **`suggest_movie`**: Get movie recommendations by genre
  - Parameters: `genre` (string)
  - Returns: Formatted list of movie recommendations

- **`get_top_movies`**: Get top-rated movies
  - Parameters: `rating` (optional string)
  - Returns: List of top-rated movies

- **`find_movies_title_cast`**: Search movies by title and cast
  - Parameters: `title` (string), `cast` (string)
  - Returns: Matching movies based on search criteria

### MCP Resources

- **`movie://database`**: Access the entire movie database
- **`movie://genres`**: Get list of all available genres
- **`movie://{movie_id}`**: Get specific movie by ID

### MCP Prompts

- **`movie_recommendation_prompt`**: Generate personalized movie recommendations
- **`movie_comparison_prompt`**: Compare multiple movies
- **`movie_search_prompt`**: Search for movies based on query

## Development

### Environment Setup

1. Create a `.env` file:
```bash
APP_ENV=dev
# Add other environment variables as needed
```

2. Configure JWT (if enabled):
```bash
JWT_SECRET_KEY=your-secret-key
```

### 🧪 Testing

The application includes comprehensive test suites:

```bash
# Run all tests
pytest

# Run MCP tools tests
pytest tests/test_mcp_tools.py -v

# Run integration tests
pytest tests/test_mcp_integration.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test class
pytest tests/test_mcp_tools.py::TestMCPToolsList -v

# Run specific test
pytest tests/test_mcp_tools.py::TestMCPToolsCall::test_call_suggest_movie_success -v
```

See `tests/README.md` for detailed test documentation.

**Test Coverage:**
- ✅ MCP tools listing (`tools/list`)
- ✅ MCP tool invocation (`tools/call`)
- ✅ Tool result formats
- ✅ Error handling (protocol errors, tool execution errors)
- ✅ Schema validation per MCP specification
- ✅ Integration tests for full workflows

## 🖥️ Connecting Claude Desktop

To connect Claude Desktop to your local FastAPI MCP server, follow these steps:

1. Open Claude Desktop and navigate to **Settings > Developer**.
2. Click on **Edit Config**. This will open the `claude_desktop_config.json` file.
![Claude Desktop Developer Settings](docs/claude_desktop_settings.png)
3. Add your server configuration to the `mcpServers` object. Here's an example:

```json
{
  "mcpServers": {
    "MyRemoteServer": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp"
      ]
    }
  }
}
```

4. Replace `"MyRemoteServer"` with a name of your choice.
5. Save the `claude_desktop_config.json` file.
6. Restart Claude Desktop for the changes to take effect.

Once connected, your server should appear as running in the settings:

![Claude Desktop Running Server](docs/claude_desktop_running_server.png)


Enter your prompt in to chat field:
"Give me some Action movies"
This shoule pop up window asking permission to talk to your Movies MCP server

![Claude Desktop Connecting to MCP server tool](docs/claude_desktop_chat_question1.png)


Claude Desktop will connect to MCP server and invoke suggsted_movies tool to fetch movies and pass to the LLM

![Claude Desktop showing LLM response after making tool call and passing tool response as context to LLM ](docs/claude_desktop_chat_answer1.png)


## 🔒 Security Features

- **JWT Authentication**: Optional, configurable per environment
- **JWKS Support**: Fetch public keys from JSON Web Key Set URLs
- **CORS Protection**: Configurable allowed origins
- **Origin Validation**: Prevents private IP access
- **Request ID Tracking**: Full request traceability
- **Error Message Sanitization**: Prevents information leakage in production
- **Secure Headers**: Production-ready security headers

## 🚀 Production Deployment

### Pre-deployment Checklist

1. **Set Environment Variables:**
   ```bash
   export APP_ENV=prod
   export JWT_SECRET_KEY=<strong-64+character-secret>
   export LOG_LEVEL=INFO
   ```

2. **Update Production Config** (`config/app_config.prod.yaml`):
   - Replace `allowed_hosts` with actual production domains
   - Configure `allowed_algorithms` (restrict to needed algorithms)
   - Ensure `JWT_SECRET_KEY` is set via environment variable

3. **Configure Logging:**
   ```bash
   export LOG_DIR=/var/log/app
   ```

4. **Verify Health Endpoints:**
   ```bash
   curl http://your-domain/health
   curl http://your-domain/ready
   ```

### Docker Production Deployment

```bash
# Build and run production container
docker-compose up --build -d

# Check logs
docker-compose logs -f app

# Scale services
docker-compose up -d --scale app=3
```

### Environment Variables for Production

```bash
APP_ENV=prod
JWT_SECRET_KEY=<your-secret-key>
ENABLE_JWT=true
LOG_LEVEL=INFO
LOG_DIR=/var/log/app
```

## 📚 Additional Resources

- [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Resources Specification](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP Prompts Specification](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)
- [FastMCP Documentation](https://gofastmcp.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Contributing

Contributions are welcome! Please ensure:
- All tests pass (`pytest`)
- Code follows project style (black, isort)
- New features include tests
- Documentation is updated

## 📄 License

MIT



