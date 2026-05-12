#!/bin/bash

# Ensure .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Build and start services
docker-compose up --build -d

echo "Services are starting. Check logs with: docker-compose logs -f"
