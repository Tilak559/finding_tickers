#!/bin/bash

echo "Starting Finding Tickers Application..."
echo "========================================"

echo ""
echo "Choose how to run the application:"
echo "Docker Compose"

echo ""
echo "Starting with Docker Compose..."
echo "========================================"

# Build and start containers
echo "Building Docker images..."
docker compose build

echo "Starting services..."
docker compose up
        
