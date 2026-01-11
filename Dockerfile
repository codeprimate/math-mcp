# Multi-stage build for smaller final image
FROM python:3.12-alpine AS builder

WORKDIR /app

# Install build dependencies only for building (removed in final stage)
RUN apk add --no-cache gcc musl-dev python3-dev

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal Alpine runtime image
FROM python:3.12-alpine

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy source code
COPY src/ src/

# Set Python path and ensure local packages are in PATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# Run the server (defaults to stdio transport, can be overridden with MCP_TRANSPORT env var)
# Port is configurable via MCP_PORT environment variable (default: 8008)
# Use -p <host-port>:<container-port> to map ports when running the container
CMD ["python", "-m", "math_mcp.server"]
