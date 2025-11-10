#!/bin/bash

echo "=========================================="
echo "Coolify Deployment Diagnostics"
echo "=========================================="
echo ""

echo "1. Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|legal|coolify-proxy|traefik"
echo ""

echo "2. Checking legal-assistant containers..."
FRONTEND=$(docker ps -q --filter "name=legal-assistant-frontend")
BACKEND=$(docker ps -q --filter "name=legal-assistant-backend")

if [ -z "$FRONTEND" ]; then
    echo "❌ Frontend container not found"
else
    echo "✅ Frontend container: $FRONTEND"
    echo "   Status: $(docker inspect $FRONTEND --format '{{.State.Status}}')"
    echo "   Health: $(docker inspect $FRONTEND --format '{{.State.Health.Status}}')"
fi

if [ -z "$BACKEND" ]; then
    echo "❌ Backend container not found"
else
    echo "✅ Backend container: $BACKEND"
    echo "   Status: $(docker inspect $BACKEND --format '{{.State.Status}}')"
    echo "   Health: $(docker inspect $BACKEND --format '{{.State.Health.Status}}')"
fi
echo ""

echo "3. Checking Traefik labels on frontend..."
if [ -n "$FRONTEND" ]; then
    docker inspect $FRONTEND --format '{{range $key, $value := .Config.Labels}}{{if or (contains $key "traefik") (contains $key "coolify")}}{{$key}}={{$value}}{{"\n"}}{{end}}{{end}}' | head -20
fi
echo ""

echo "4. Checking Traefik labels on backend..."
if [ -n "$BACKEND" ]; then
    docker inspect $BACKEND --format '{{range $key, $value := .Config.Labels}}{{if or (contains $key "traefik") (contains $key "coolify")}}{{$key}}={{$value}}{{"\n"}}{{end}}{{end}}' | head -20
fi
echo ""

echo "5. Checking proxy container..."
PROXY=$(docker ps -q --filter "name=coolify-proxy")
if [ -z "$PROXY" ]; then
    echo "❌ Coolify proxy not found"
else
    echo "✅ Coolify proxy: $PROXY"
    echo "   Recent logs mentioning ailegal:"
    docker logs $PROXY 2>&1 | tail -100 | grep -i "ailegal" | tail -5
fi
echo ""

echo "6. Testing internal connectivity..."
if [ -n "$FRONTEND" ]; then
    echo "Testing frontend (should return HTML):"
    docker exec $FRONTEND wget -q -O- http://localhost:3001 2>&1 | head -5
fi

if [ -n "$BACKEND" ]; then
    echo "Testing backend health:"
    docker exec $BACKEND curl -s http://localhost:8080/health
fi
echo ""

echo "7. Checking DNS resolution..."
nslookup ailegal.mehh.ae | grep -A 2 "answer:"
echo ""

echo "=========================================="
echo "Diagnostics complete!"
echo "=========================================="
