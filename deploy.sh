#!/bin/bash

# AI Legal Assistant - Docker Deployment Script
# This script helps you quickly deploy the application using Docker Compose

set -e

echo "========================================="
echo "AI Legal Assistant - Docker Deployment"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "Warning: .env.production not found!"
    echo ""
    echo "Creating .env.production from template..."
    cp .env.production.example .env.production
    echo ""
    echo "Please edit .env.production and set your GOOGLE_API_KEY"
    echo "Then run this script again."
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if grep -q "your_google_api_key_here" .env.production; then
    echo "Error: Please set your GOOGLE_API_KEY in .env.production"
    exit 1
fi

echo "Step 1: Building Docker images..."
docker-compose -f docker-compose.local.yml build

echo ""
echo "Step 2: Starting services..."
docker-compose -f docker-compose.local.yml up -d

echo ""
echo "Step 3: Waiting for services to be healthy..."
sleep 10

# Check backend health
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✓ Backend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Backend health check failed"
        docker-compose logs backend
        exit 1
    fi
    sleep 2
done

# Check frontend health
echo "Checking frontend health..."
for i in {1..30}; do
    if curl -f http://localhost:3000 &> /dev/null; then
        echo "✓ Frontend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Frontend health check failed"
        docker-compose logs frontend
        exit 1
    fi
    sleep 2
done

echo ""
echo "========================================="
echo "Deployment Successful!"
echo "========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Go to the Policies page and upload your company policies"
echo "3. Click 'Reingest Policies' to update the vector database"
echo "4. Start analyzing contracts!"
echo ""
echo "To view logs: docker-compose -f docker-compose.local.yml logs -f"
echo "To stop: docker-compose -f docker-compose.local.yml down"
echo ""
