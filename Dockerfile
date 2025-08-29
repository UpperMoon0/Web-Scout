# Web-Scout Dockerfile - Embedded MCP Architecture
# Unified server supporting both HTTP REST API and JSON-RPC MCP over HTTP
# Updated from: Separate MCP server entry point
# Updated to: Embedded MCP within REST API server

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Web-Scout directory content to the working directory
COPY . /app/Web-Scout

# Copy and set environment file
COPY .env* /app/Web-Scout/

# Set working directory to the application directory
WORKDIR /app/Web-Scout

# Add current directory to Python path to enable relative imports
ENV PYTHONPATH=/app/Web-Scout:$PYTHONPATH

# Expose the port the app runs on
EXPOSE 8000

# Single unified server - supports both HTTP REST API and Embedded MCP
CMD ["python", "main.py"]