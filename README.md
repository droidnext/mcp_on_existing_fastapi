# FastAPI MCP Application

A FastAPI application with Model Context Protocol (MCP) integration for AI tools.

## Features

- FastAPI backend with MCP integration
- Movie recommendation and search tools
- JWT authentication (configurable)
- Arize Phoenix integration (configurable)
- Environment-specific configurations

## Prerequisites

- Python 3.8+
- Node.js 14+ (for MCP inspector)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install MCP inspector:
```bash
npm install @modelcontextprotocol/inspector
```

## Configuration

The application uses environment-specific YAML configuration files in the `config` directory:

- `app_config.dev.yaml`: Development settings
- `app_config.prod.yaml`: Production settings

You can override settings using environment variables or a `.env` file.

### Key Configuration Options

- `APP_ENV`: Set to 'dev' or 'prod' to use different configurations
- `ENABLE_JWT`: Toggle JWT authentication
- `ENABLE_ARIZE`: Toggle Arize Phoenix instrumentation
- `MCP_TOOL_TIMEOUT`: Set timeout for MCP tools

## Running the Application

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

## API Endpoints

- `/api/v1/movies`: Movie-related endpoints
- `/mcp`: MCP tools and endpoints
- `/routes`: List all available routes

## MCP Tools

The application provides the following MCP tools:

- `suggest_movie`: Get movie recommendations by genre
- `get_top_movies`: Get top-rated movies
- `search_movies`: Search movies by title, description, or cast

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

### Testing

```bash
pytest
```

## License

[Your License]
