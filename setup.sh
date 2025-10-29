#!/bin/bash

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env

# Start Redis
docker run --rm -d -p 6379:6379 redis:7-alpine

echo "Setup complete. Run the agent with: python agents/content_distribution_agent.py --content content.txt"