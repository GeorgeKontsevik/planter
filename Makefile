SHELL := /bin/bash

# Default environment variables
HOST = 0.0.0.0
PORT = 8000
APP = api.app.main:app
WORKERS = 1
RELOAD = --reload

# Run FastAPI in development mode
run:
	uvicorn $(APP) --host $(HOST) --port $(PORT) $(RELOAD)

# Run FastAPI in production mode
prod:
	uvicorn $(APP) --host $(HOST) --port $(PORT) --workers $(WORKERS)

# Clean up Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Kill the process using the specified port
killport:
	lsof -ti :$(PORT) | xargs kill -9 || echo "No process is using port $(PORT)"

# Install Python dependencies
install:
	pip install -r reqs.txt

# Run tests
test:
	pytest tests/

# Lint code
lint:
	flake8 .

# Format code
format:
	black .